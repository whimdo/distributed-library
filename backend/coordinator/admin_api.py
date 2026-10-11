from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request

from backend.common.models import (
    AuthUser,
    BorrowAdminCreate,
    BorrowAdminUpdate,
    CopyAdminCreate,
    CopyAdminUpdate,
    LibraryAdminCreate,
    LibraryAdminUpdate,
    ReaderAdminCreate,
    ReaderAdminUpdate,
    SiteExecuteRequest,
)
from backend.coordinator.auth import AdminUser


router = APIRouter(prefix="/api/admin", tags=["admin"])
STUDENT_DEMO_PASSWORD_HASH = "pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k"


def _resolve_sites(user: AuthUser, requested_site: int | None) -> list[int]:
    if requested_site is not None and requested_site not in {1, 2, 3}:
        raise HTTPException(status_code=400, detail="site_id 必须为 1、2 或 3。")
    if user.role == "SITE_ADMIN":
        if requested_site is not None and requested_site != user.managed_site_id:
            raise HTTPException(status_code=403, detail="站点管理员不能访问其他站点。")
        return [int(user.managed_site_id)]
    return [requested_site] if requested_site else [1, 2, 3]


async def _query_sites(
    request: Request,
    site_ids: list[int],
    sql: str,
) -> list[dict[str, object]]:
    query_id = uuid4().hex
    result = await request.app.state.site_client.execute_many(
        site_ids,
        SiteExecuteRequest(query_id=query_id, sql=sql),
    )
    rows: list[dict[str, object]] = []
    for site_result in result:
        for row in site_result.rows:
            rows.append({**row, "data_site_id": site_result.site_id})
    return rows


@router.get("/context")
async def context(user: AdminUser, request: Request) -> dict[str, object]:
    site = None
    if user.managed_site_id:
        site = await request.app.state.coordinator_pool.fetchrow(
            "SELECT site_id, site_name, region_name FROM site_node WHERE site_id = $1",
            user.managed_site_id,
        )
    return {
        "role": user.role,
        "scope": "ALL_SITES" if user.role == "ADMIN" else "SINGLE_SITE",
        "managed_site": dict(site) if site else None,
    }


@router.get("/overview")
async def overview(
    request: Request,
    user: AdminUser,
    site_id: int | None = Query(default=None),
) -> dict[str, object]:
    sites = _resolve_sites(user, site_id)
    statements = {
        "libraries": "SELECT COUNT(*) AS total FROM library_fragment",
        "readers": "SELECT COUNT(*) AS total FROM reader_fragment",
        "copies": "SELECT COUNT(*) AS total FROM book_copy_fragment",
        "borrow_records": "SELECT COUNT(*) AS total FROM borrow_record_fragment",
    }
    results = await asyncio.gather(*(
        _query_sites(request, sites, sql) for sql in statements.values()
    ))
    counts = {
        name: sum(int(row.get("total", 0)) for row in rows)
        for name, rows in zip(statements, results)
    }
    campus_count = await request.app.state.coordinator_pool.fetchval(
        "SELECT COUNT(*) FROM campus WHERE site_id = ANY($1::smallint[])", sites
    )
    return {"site_ids": sites, "campuses": campus_count, **counts}


@router.get("/gis")
async def gis_layers(
    request: Request,
    user: AdminUser,
    site_id: int | None = Query(default=None),
) -> dict[str, object]:
    """Return only the GIS layers visible to the current administrator."""
    sites = _resolve_sites(user, site_id)
    site_records = await request.app.state.coordinator_pool.fetch("""
        SELECT site_id, site_name, region_name,
               ST_AsGeoJSON(region_geometry) AS geometry
        FROM site_node
        WHERE site_id = ANY($1::smallint[])
        ORDER BY site_id
    """, sites)
    campus_records = await request.app.state.coordinator_pool.fetch("""
        SELECT campus_id, university_id, campus_name, address,
               longitude, latitude, site_id, ST_AsGeoJSON(boundary) AS geometry
        FROM campus
        WHERE site_id = ANY($1::smallint[])
        ORDER BY campus_id
    """, sites)
    libraries = await _query_sites(request, sites, """
        SELECT library_id, library_name, campus_id, address, longitude,
               latitude, total_seats, status
        FROM library_fragment ORDER BY library_id LIMIT 100
    """)
    return {
        "site_ids": sites,
        "sites": [dict(record) for record in site_records],
        "campuses": [dict(record) for record in campus_records],
        "libraries": libraries,
    }


@router.get("/readers")
async def readers(
    request: Request,
    user: AdminUser,
    site_id: int | None = Query(default=None),
) -> dict[str, object]:
    sites = _resolve_sites(user, site_id)
    rows = await _query_sites(request, sites, """
        SELECT reader_id, home_university_id, home_campus_id, student_no,
               network_card_no, reader_name, phone, email, reader_type, network_permission,
               max_borrow_count, current_borrow_count, status
        FROM reader_fragment ORDER BY reader_id LIMIT 200
    """)
    return {"site_ids": sites, "rows": rows, "row_count": len(rows)}


@router.get("/copies")
async def copies(
    request: Request,
    user: AdminUser,
    site_id: int | None = Query(default=None),
) -> dict[str, object]:
    sites = _resolve_sites(user, site_id)
    rows = await _query_sites(request, sites, """
        SELECT copy_id, book_id, owner_university_id, owner_campus_id, owner_library_id,
               current_library_id, barcode, shelf_location, copy_status,
               allow_cross_borrow, acquisition_date, price
        FROM book_copy_fragment ORDER BY copy_id LIMIT 200
    """)
    book_ids = sorted({int(row["book_id"]) for row in rows})
    titles: dict[int, str] = {}
    if book_ids:
        records = await request.app.state.coordinator_pool.fetch(
            "SELECT book_id, title FROM book_catalog WHERE book_id = ANY($1::bigint[])",
            book_ids,
        )
        titles = {int(record["book_id"]): record["title"] for record in records}
    for row in rows:
        row["title"] = titles.get(int(row["book_id"]), "未知书目")
    return {"site_ids": sites, "rows": rows, "row_count": len(rows)}


@router.get("/borrow-records")
async def borrow_records(
    request: Request,
    user: AdminUser,
    site_id: int | None = Query(default=None),
) -> dict[str, object]:
    sites = _resolve_sites(user, site_id)
    rows = await _query_sites(request, sites, """
        SELECT borrow_id, reader_id, reader_home_campus_id, book_id, copy_id,
               copy_owner_site_id, checkout_library_id, return_library_id,
               borrow_type, borrow_time, due_time, return_time,
               borrow_status, renew_count, fine_amount
        FROM borrow_record_fragment ORDER BY borrow_time DESC LIMIT 200
    """)
    return {"site_ids": sites, "rows": rows, "row_count": len(rows)}


@router.patch("/readers/{reader_id}")
async def update_reader(
    reader_id: int,
    update: ReaderAdminUpdate,
    request: Request,
    user: AdminUser,
    site_id: int = Query(...),
) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    update.query_id = update.query_id or uuid4().hex
    return await request.app.state.site_client.update_reader(target, reader_id, update)


@router.patch("/copies/{copy_id}")
async def update_copy(
    copy_id: int,
    update: CopyAdminUpdate,
    request: Request,
    user: AdminUser,
    site_id: int = Query(...),
) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    update.query_id = update.query_id or uuid4().hex
    return await request.app.state.site_client.update_copy(target, copy_id, update)


@router.get("/libraries")
async def libraries(request: Request, user: AdminUser, site_id: int | None = Query(default=None)) -> dict[str, object]:
    sites = _resolve_sites(user, site_id)
    rows = await _query_sites(request, sites, """
        SELECT library_id, university_id, campus_id, library_name, address,
               longitude, latitude, open_time, close_time, phone, total_seats,
               service_radius_m, status
        FROM library_fragment ORDER BY library_id LIMIT 200
    """)
    return {"site_ids": sites, "rows": rows, "row_count": len(rows)}


@router.get("/metadata")
async def metadata(request: Request, user: AdminUser, site_id: int | None = Query(default=None)) -> dict[str, object]:
    sites = _resolve_sites(user, site_id)
    universities = await request.app.state.coordinator_pool.fetch(
        "SELECT university_id, university_name, short_name FROM university WHERE status='ACTIVE' ORDER BY university_id"
    )
    campuses = await request.app.state.coordinator_pool.fetch("""
        SELECT campus_id, university_id, campus_name, site_id, address,
               longitude, latitude, ST_AsGeoJSON(boundary) AS boundary_geojson
        FROM campus WHERE site_id=ANY($1::smallint[]) AND status='ACTIVE' ORDER BY campus_id
    """, sites)
    books = await request.app.state.coordinator_pool.fetch(
        "SELECT book_id,title,isbn FROM book_catalog ORDER BY book_id"
    )
    library_rows = await _query_sites(request, sites, """
        SELECT library_id,university_id,campus_id,library_name FROM library_fragment ORDER BY library_id
    """)
    reader_rows = await _query_sites(request, sites, """
        SELECT reader_id,reader_name,home_campus_id FROM reader_fragment ORDER BY reader_id
    """)
    copy_rows = await _query_sites(request, sites, """
        SELECT copy_id,book_id,owner_campus_id,owner_library_id FROM book_copy_fragment ORDER BY copy_id
    """)
    return {"site_ids": sites, "universities": [dict(r) for r in universities],
            "campuses": [dict(r) for r in campuses], "books": [dict(r) for r in books],
            "libraries": library_rows, "readers": reader_rows, "copies": copy_rows}


async def _validate_campus(request: Request, site_id: int, campus_id: int, university_id: int) -> None:
    valid = await request.app.state.coordinator_pool.fetchval(
        "SELECT EXISTS(SELECT 1 FROM campus WHERE campus_id=$1 AND university_id=$2 AND site_id=$3 AND status='ACTIVE')",
        campus_id, university_id, site_id,
    )
    if not valid:
        raise HTTPException(status_code=400, detail="高校、校区与数据站点的归属关系不匹配。")


@router.post("/readers")
async def create_reader(update: ReaderAdminCreate, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    await _validate_campus(request, target, update.home_campus_id, update.home_university_id)
    update.query_id = uuid4().hex
    result = await request.app.state.site_client.create_resource(target, "readers", update.model_dump(mode="json"))
    try:
        await request.app.state.coordinator_pool.execute("""
            INSERT INTO user_account (username,password_hash,display_name,role,reader_id,home_site_id,account_status)
            VALUES ($1,$2,$3,'STUDENT',$4,$5,'ACTIVE')
        """, update.student_no, STUDENT_DEMO_PASSWORD_HASH, update.reader_name, result["reader_id"], target)
    except Exception:
        await request.app.state.site_client.delete_resource(target, f"readers/{result['reader_id']}", update.query_id)
        raise
    return {**result, "data_site_id": target, "login_username": update.student_no, "initial_password": "student123"}


@router.delete("/readers/{reader_id}")
async def delete_reader(reader_id: int, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    result = await request.app.state.site_client.delete_resource(target, f"readers/{reader_id}", uuid4().hex)
    await request.app.state.coordinator_pool.execute("DELETE FROM user_account WHERE reader_id=$1", reader_id)
    return result


@router.post("/copies")
async def create_copy(update: CopyAdminCreate, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    await _validate_campus(request, target, update.owner_campus_id, update.owner_university_id)
    update.query_id = uuid4().hex
    return await request.app.state.site_client.create_resource(target, "copies", update.model_dump(mode="json"))


@router.delete("/copies/{copy_id}")
async def delete_copy(copy_id: int, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    return await request.app.state.site_client.delete_resource(target, f"copies/{copy_id}", uuid4().hex)


@router.post("/borrow-records")
async def create_borrow(update: BorrowAdminCreate, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]; update.query_id = uuid4().hex
    return await request.app.state.site_client.create_resource(target, "borrow-records", update.model_dump(mode="json"))


@router.patch("/borrow-records/{borrow_id}")
async def update_borrow(borrow_id: int, update: BorrowAdminUpdate, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]; update.query_id = uuid4().hex
    return await request.app.state.site_client.update_resource(target, f"borrow-records/{borrow_id}", update.model_dump(mode="json"))


@router.delete("/borrow-records/{borrow_id}")
async def delete_borrow(borrow_id: int, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    return await request.app.state.site_client.delete_resource(target, f"borrow-records/{borrow_id}", uuid4().hex)


@router.post("/libraries")
async def create_library(update: LibraryAdminCreate, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    await _validate_campus(request, target, update.campus_id, update.university_id)
    update.query_id = uuid4().hex
    return await request.app.state.site_client.create_resource(target, "libraries", update.model_dump(mode="json"))


@router.patch("/libraries/{library_id}")
async def update_library(library_id: int, update: LibraryAdminUpdate, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]; update.query_id = uuid4().hex
    return await request.app.state.site_client.update_resource(target, f"libraries/{library_id}", update.model_dump(mode="json"))


@router.delete("/libraries/{library_id}")
async def delete_library(library_id: int, request: Request, user: AdminUser, site_id: int = Query(...)) -> dict[str, object]:
    target = _resolve_sites(user, site_id)[0]
    return await request.app.state.site_client.delete_resource(target, f"libraries/{library_id}", uuid4().hex)
