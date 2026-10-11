from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Query, Request

from backend.common.models import SiteExecuteRequest
from backend.coordinator.auth import StudentUser


router = APIRouter(prefix="/api", tags=["portal"])


@router.get("/public/books")
async def search_books(
    request: Request,
    q: str = Query(default="", max_length=100),
    category_id: int | None = Query(default=None),
    library_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, object]:
    pattern = f"%{q.strip()}%"
    book_ids: list[int] | None = None
    if library_id is not None:
        inventory = await request.app.state.site_client.execute_many(
            [1, 2, 3],
            SiteExecuteRequest(query_id=uuid4().hex, sql=f"""
                SELECT DISTINCT book_id FROM book_copy_fragment
                WHERE current_library_id={int(library_id)} ORDER BY book_id
            """),
        )
        book_ids = [int(row["book_id"]) for result in inventory for row in result.rows]
        if not book_ids:
            return {"rows": [], "row_count": 0}
    records = await request.app.state.coordinator_pool.fetch("""
        SELECT b.book_id, b.isbn, b.title, b.author, b.publisher,
               b.publish_year, b.edition, b.language, b.page_count,
               b.summary, b.keywords, b.cover_url, b.category_id, c.category_name
        FROM book_catalog b
        JOIN category c ON c.category_id = b.category_id
        WHERE ($1 = '%%' OR b.title ILIKE $1 OR COALESCE(b.author, '') ILIKE $1
           OR COALESCE(b.isbn, '') ILIKE $1 OR COALESCE(b.keywords, '') ILIKE $1)
          AND ($2::bigint IS NULL OR b.category_id=$2)
          AND ($3::bigint[] IS NULL OR b.book_id=ANY($3))
        ORDER BY b.book_id
        LIMIT $4
    """, pattern, category_id, book_ids, limit)
    return {"rows": [dict(record) for record in records], "row_count": len(records)}


@router.get("/public/catalog-options")
async def catalog_options(request: Request) -> dict[str, object]:
    categories = await request.app.state.coordinator_pool.fetch(
        "SELECT category_id,category_name FROM category WHERE status='ACTIVE' ORDER BY sort_order,category_id"
    )
    libraries = await public_libraries(request)
    return {"categories": [dict(row) for row in categories], "libraries": libraries["rows"]}


@router.get("/public/books/{book_id}")
async def book_detail(book_id: int, request: Request) -> dict[str, object]:
    book = await request.app.state.coordinator_pool.fetchrow("""
        SELECT b.*,c.category_name FROM book_catalog b
        JOIN category c ON c.category_id=b.category_id WHERE b.book_id=$1
    """, book_id)
    if not book:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="书目不存在。")
    results = await request.app.state.site_client.execute_many([1,2,3], SiteExecuteRequest(
        query_id=uuid4().hex,
        sql=f"""SELECT c.copy_id,c.copy_status,c.allow_cross_borrow,c.shelf_location,
                       c.owner_university_id,c.owner_campus_id,c.current_library_id,
                       l.library_name,l.address,l.longitude,l.latitude
                FROM book_copy_fragment c JOIN library_fragment l
                  ON l.library_id=c.current_library_id
                WHERE c.book_id={int(book_id)} ORDER BY c.copy_id""",
    ))
    copies = [{**row,"site_id":result.site_id} for result in results for row in result.rows]
    university_ids = sorted({int(row["owner_university_id"]) for row in copies})
    campus_ids = sorted({int(row["owner_campus_id"]) for row in copies})
    universities = await request.app.state.coordinator_pool.fetch(
        "SELECT university_id,university_name FROM university WHERE university_id=ANY($1::bigint[])", university_ids
    ) if university_ids else []
    campuses = await request.app.state.coordinator_pool.fetch(
        "SELECT campus_id,campus_name FROM campus WHERE campus_id=ANY($1::bigint[])", campus_ids
    ) if campus_ids else []
    university_names={int(r["university_id"]):r["university_name"] for r in universities}
    campus_names={int(r["campus_id"]):r["campus_name"] for r in campuses}
    for copy in copies:
        copy["university_name"]=university_names.get(int(copy["owner_university_id"]),"未知高校")
        copy["campus_name"]=campus_names.get(int(copy["owner_campus_id"]),"未知校区")
    schools=sorted({str(copy["university_name"]) for copy in copies})
    return {"book": dict(book), "copies": copies, "schools": schools,
            "copy_count": len(copies),
            "available_count": sum(1 for copy in copies if copy["copy_status"]=="AVAILABLE")}


@router.get("/public/libraries")
async def public_libraries(request: Request) -> dict[str, object]:
    result = await request.app.state.site_client.execute_many(
        [1, 2, 3],
        SiteExecuteRequest(
            query_id=uuid4().hex,
            sql="""
                SELECT library_id, library_name, campus_id, address,
                       longitude, latitude, open_time, close_time,
                       total_seats, service_radius_m, status
                FROM library_fragment ORDER BY library_id LIMIT 100
            """,
        ),
    )
    rows = [
        {**row, "site_id": site_result.site_id}
        for site_result in result
        for row in site_result.rows
    ]
    return {"rows": rows, "row_count": len(rows)}


@router.get("/public/libraries/nearby")
async def nearby_libraries(
    request: Request,
    longitude: float = Query(..., ge=-180, le=180),
    latitude: float = Query(..., ge=-90, le=90),
    radius_km: float = Query(default=10, gt=0, le=100),
) -> dict[str, object]:
    """Run the same indexed PostGIS distance query at every data site."""
    point = (
        f"ST_SetSRID(ST_MakePoint({longitude:.8f}, {latitude:.8f}), 4326)"
        "::geography"
    )
    result = await request.app.state.site_client.execute_many(
        [1, 2, 3],
        SiteExecuteRequest(
            query_id=uuid4().hex,
            sql=f"""
                SELECT library_id, library_name, campus_id, address,
                       longitude, latitude, open_time, close_time,
                       total_seats, service_radius_m, status,
                       ROUND(ST_Distance(location, {point})::numeric, 0) AS distance_m
                FROM library_fragment
                WHERE ST_DWithin(location, {point}, {radius_km * 1000:.2f})
                ORDER BY distance_m LIMIT 100
            """,
        ),
    )
    rows = sorted(
        (
            {**row, "site_id": site_result.site_id}
            for site_result in result
            for row in site_result.rows
        ),
        key=lambda row: float(row["distance_m"]),
    )
    return {"rows": rows, "row_count": len(rows), "radius_km": radius_km}


@router.get("/portal/me/borrowings")
async def my_borrowings(
    request: Request,
    user: StudentUser,
) -> dict[str, object]:
    result = await request.app.state.site_client.execute(
        int(user.home_site_id),
        SiteExecuteRequest(
            query_id=uuid4().hex,
            sql=f"""
                SELECT borrow_id, book_id, copy_id, copy_owner_site_id,
                       checkout_library_id, return_library_id, borrow_type,
                       borrow_time, due_time, return_time, borrow_status,
                       renew_count, fine_amount
                FROM borrow_record_fragment
                WHERE reader_id = {int(user.reader_id)}
                ORDER BY borrow_time DESC LIMIT 100
            """,
        ),
    )
    book_ids = sorted({int(row["book_id"]) for row in result.rows})
    titles: dict[int, str] = {}
    if book_ids:
        records = await request.app.state.coordinator_pool.fetch(
            "SELECT book_id, title FROM book_catalog WHERE book_id = ANY($1::bigint[])",
            book_ids,
        )
        titles = {int(record["book_id"]): record["title"] for record in records}
    rows = [{**row, "title": titles.get(int(row["book_id"]), "未知书目")} for row in result.rows]
    return {"reader_id": user.reader_id, "rows": rows, "row_count": len(rows)}
