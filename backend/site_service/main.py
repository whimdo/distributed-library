from __future__ import annotations

import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.common.config import get_settings
from backend.common.event_bus import EventBus
from backend.common.models import (
    BorrowAdminCreate,
    BorrowAdminUpdate,
    CopyAdminCreate,
    CopyAdminUpdate,
    LibraryAdminCreate,
    LibraryAdminUpdate,
    ReaderAdminCreate,
    ReaderAdminUpdate,
    SiteExecuteRequest,
    SiteExecuteResponse,
)
from backend.common.serialization import record_to_dict
from backend.site_service.security import (
    PhysicalQueryValidationError,
    validate_physical_query,
)


settings = get_settings()
site_id = int(os.getenv("SITE_ID", "1"))
if site_id not in {1, 2, 3}:
    raise RuntimeError("SITE_ID must be 1, 2, or 3")
database_name = f"site{site_id}_db"
event_bus = EventBus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        dsn=settings.site_database_urls[site_id],
        min_size=1,
        max_size=5,
        command_timeout=settings.query_timeout_seconds,
    )
    yield
    await app.state.pool.close()


app = FastAPI(
    title=f"Distributed Library Site {site_id}",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, object]:
    async with app.state.pool.acquire() as connection:
        database = await connection.fetchval("SELECT current_database()")
    return {
        "service": f"site{site_id}",
        "site_id": site_id,
        "database": database,
        "status": "healthy",
    }


@app.post("/internal/execute", response_model=SiteExecuteResponse)
async def execute(
    request: SiteExecuteRequest,
    x_internal_token: str | None = Header(default=None),
) -> SiteExecuteResponse:
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="无效的内部服务令牌。")
    try:
        validate_physical_query(request.sql)
    except PhysicalQueryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await event_bus.publish(
        request.query_id,
        f"site{site_id}",
        "COMMAND_RECEIVED",
        f"Site {site_id} 收到主节点物理查询。",
        {"sql": request.sql},
    )
    await event_bus.publish(
        request.query_id,
        f"site{site_id}",
        "LOCAL_SQL_EXECUTING",
        f"在 {database_name} 执行 SQL。",
        {"sql": request.sql},
    )
    try:
        async with app.state.pool.acquire() as connection:
            records = await connection.fetch(
                request.sql,
                timeout=settings.query_timeout_seconds,
            )
    except asyncpg.PostgresError as exc:
        await event_bus.publish(
            request.query_id,
            f"site{site_id}",
            "ERROR_OCCURRED",
            f"本地 SQL 执行失败：{exc}",
        )
        raise HTTPException(status_code=400, detail=f"本地 SQL 执行失败：{exc}") from exc

    rows = [record_to_dict(record) for record in records]
    columns = list(records[0].keys()) if records else []
    await event_bus.publish(
        request.query_id,
        f"site{site_id}",
        "LOCAL_RESULT_CREATED",
        f"Site {site_id} 生成 {len(rows)} 行结果。",
        {"row_count": len(rows)},
    )
    await event_bus.publish(
        request.query_id,
        f"site{site_id}",
        "RESULT_SENT",
        f"Site {site_id} 向主节点返回结果。",
        {"row_count": len(rows)},
    )
    return SiteExecuteResponse(
        query_id=request.query_id,
        site_id=site_id,
        database=database_name,
        columns=columns,
        rows=rows,
        row_count=len(rows),
    )


def _check_internal_token(token: str | None) -> None:
    if token != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="无效的内部服务令牌。")


async def _publish_change(query_id: str, event_type: str, message: str, details: dict[str, object]) -> None:
    await event_bus.publish(query_id, f"site{site_id}", event_type, message, details)


@app.patch("/internal/admin/readers/{reader_id}")
async def update_reader(
    reader_id: int,
    request: ReaderAdminUpdate,
    x_internal_token: str | None = Header(default=None),
) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    allowed_statuses = {"ACTIVE", "FROZEN", "DISABLED"}
    if request.status is not None and request.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="无效的读者状态。")
    assignments: list[str] = []
    values: list[object] = []
    for column, value in (
        ("status", request.status),
        ("network_permission", request.network_permission),
        ("max_borrow_count", request.max_borrow_count),
        ("reader_name", request.reader_name),
        ("phone", request.phone),
        ("email", request.email),
        ("reader_type", request.reader_type),
    ):
        if value is not None:
            values.append(value)
            assignments.append(f"{column} = ${len(values)}")
    if not assignments:
        raise HTTPException(status_code=400, detail="没有需要更新的读者字段。")
    values.append(reader_id)
    sql = f"""
        UPDATE reader_fragment
        SET {', '.join(assignments)}, updated_at = CURRENT_TIMESTAMP
        WHERE reader_id = ${len(values)}
        RETURNING reader_id, reader_name, home_campus_id, reader_type,
                  network_permission, max_borrow_count,
                  current_borrow_count, status
    """
    try:
        async with app.state.pool.acquire() as connection:
            record = await connection.fetchrow(sql, *values)
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=400, detail=f"读者更新失败：{exc}") from exc
    if record is None:
        raise HTTPException(status_code=404, detail="本站点不存在该读者。")
    await event_bus.publish(
        request.query_id, f"site{site_id}", "READER_UPDATED",
        f"Site {site_id} 更新读者 {reader_id}。",
        {"reader_id": reader_id},
    )
    return record_to_dict(record)


@app.post("/internal/admin/readers")
async def create_reader(request: ReaderAdminCreate, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    if request.reader_type not in {"UNDERGRADUATE", "POSTGRADUATE", "TEACHER"}:
        raise HTTPException(status_code=400, detail="无效的读者类型。")
    if request.status not in {"ACTIVE", "FROZEN", "DISABLED"}:
        raise HTTPException(status_code=400, detail="无效的读者状态。")
    try:
        async with app.state.pool.acquire() as connection, connection.transaction():
            await connection.execute("LOCK TABLE reader_fragment IN EXCLUSIVE MODE")
            base = site_id * 100_000_000_000
            reader_id = await connection.fetchval("SELECT GREATEST(COALESCE(MAX(reader_id), $1), $1) + 1 FROM reader_fragment", base)
            record = await connection.fetchrow("""
                INSERT INTO reader_fragment (
                    reader_id, home_university_id, home_campus_id, student_no,
                    network_card_no, reader_name, phone, email, password_hash,
                    reader_type, network_permission, max_borrow_count, status
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                RETURNING *
            """, reader_id, request.home_university_id, request.home_campus_id,
                request.student_no, request.network_card_no, request.reader_name,
                request.phone, request.email, "managed-by-central-auth",
                request.reader_type, request.network_permission,
                request.max_borrow_count, request.status)
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=400, detail=f"读者新增失败：{exc}") from exc
    await _publish_change(request.query_id, "READER_CREATED", f"Site {site_id} 新增读者 {reader_id}。", {"reader_id": reader_id})
    return record_to_dict(record)


@app.delete("/internal/admin/readers/{reader_id}")
async def delete_reader(reader_id: int, query_id: str, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    try:
        async with app.state.pool.acquire() as connection:
            record = await connection.fetchrow("DELETE FROM reader_fragment WHERE reader_id=$1 RETURNING reader_id, student_no, reader_name", reader_id)
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=409, detail=f"读者仍有关联借阅记录，不能删除：{exc}") from exc
    if not record: raise HTTPException(status_code=404, detail="本站点不存在该读者。")
    await _publish_change(query_id, "READER_DELETED", f"Site {site_id} 删除读者 {reader_id}。", {"reader_id": reader_id})
    return record_to_dict(record)


@app.patch("/internal/admin/copies/{copy_id}")
async def update_copy(
    copy_id: int,
    request: CopyAdminUpdate,
    x_internal_token: str | None = Header(default=None),
) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    allowed_statuses = {"AVAILABLE", "BORROWED", "IN_TRANSIT", "REPAIR", "LOST"}
    if request.copy_status is not None and request.copy_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="无效的馆藏状态。")
    assignments: list[str] = []
    values: list[object] = []
    for column, value in (
        ("copy_status", request.copy_status),
        ("allow_cross_borrow", request.allow_cross_borrow),
        ("shelf_location", request.shelf_location),
        ("current_library_id", request.current_library_id),
        ("acquisition_date", request.acquisition_date),
        ("price", request.price),
    ):
        if value is not None:
            values.append(value)
            assignments.append(f"{column} = ${len(values)}")
    if not assignments:
        raise HTTPException(status_code=400, detail="没有需要更新的馆藏字段。")
    values.append(copy_id)
    sql = f"""
        UPDATE book_copy_fragment
        SET {', '.join(assignments)}, updated_at = CURRENT_TIMESTAMP
        WHERE copy_id = ${len(values)}
        RETURNING copy_id, book_id, owner_campus_id, current_library_id,
                  barcode, shelf_location, copy_status, allow_cross_borrow
    """
    async with app.state.pool.acquire() as connection:
        record = await connection.fetchrow(sql, *values)
    if record is None:
        raise HTTPException(status_code=404, detail="本站点不存在该馆藏。")
    await event_bus.publish(
        request.query_id, f"site{site_id}", "COPY_UPDATED",
        f"Site {site_id} 更新馆藏 {copy_id}。",
        {"copy_id": copy_id},
    )
    return record_to_dict(record)


@app.post("/internal/admin/copies")
async def create_copy(request: CopyAdminCreate, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    if request.copy_status not in {"AVAILABLE", "BORROWED", "IN_TRANSIT", "REPAIR", "LOST"}:
        raise HTTPException(status_code=400, detail="无效的馆藏状态。")
    try:
        async with app.state.pool.acquire() as connection, connection.transaction():
            await connection.execute("LOCK TABLE book_copy_fragment IN EXCLUSIVE MODE")
            base = site_id * 100_000_000_000
            copy_id = await connection.fetchval("SELECT GREATEST(COALESCE(MAX(copy_id), $1), $1) + 1 FROM book_copy_fragment", base)
            record = await connection.fetchrow("""
                INSERT INTO book_copy_fragment (copy_id,book_id,owner_university_id,owner_campus_id,owner_library_id,current_library_id,barcode,shelf_location,copy_status,allow_cross_borrow,acquisition_date,price)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING *
            """, copy_id, request.book_id, request.owner_university_id, request.owner_campus_id,
                request.owner_library_id, request.current_library_id, request.barcode,
                request.shelf_location, request.copy_status, request.allow_cross_borrow,
                request.acquisition_date, request.price)
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=400, detail=f"馆藏新增失败：{exc}") from exc
    await _publish_change(request.query_id, "COPY_CREATED", f"Site {site_id} 新增馆藏 {copy_id}。", {"copy_id": copy_id})
    return record_to_dict(record)


@app.delete("/internal/admin/copies/{copy_id}")
async def delete_copy(copy_id: int, query_id: str, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    try:
        async with app.state.pool.acquire() as connection:
            record = await connection.fetchrow("DELETE FROM book_copy_fragment WHERE copy_id=$1 RETURNING copy_id, barcode", copy_id)
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=409, detail=f"馆藏仍有关联借阅记录，不能删除：{exc}") from exc
    if not record: raise HTTPException(status_code=404, detail="本站点不存在该馆藏。")
    await _publish_change(query_id, "COPY_DELETED", f"Site {site_id} 删除馆藏 {copy_id}。", {"copy_id": copy_id})
    return record_to_dict(record)


@app.post("/internal/admin/borrow-records")
async def create_borrow(request: BorrowAdminCreate, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    try:
        async with app.state.pool.acquire() as connection, connection.transaction():
            await connection.execute("LOCK TABLE borrow_record_fragment IN EXCLUSIVE MODE")
            base = site_id * 100_000_000_000
            borrow_id = await connection.fetchval("SELECT GREATEST(COALESCE(MAX(borrow_id), $1), $1) + 1 FROM borrow_record_fragment", base)
            record = await connection.fetchrow("""
                INSERT INTO borrow_record_fragment (borrow_id,reader_id,reader_home_campus_id,book_id,copy_id,copy_owner_site_id,checkout_library_id,return_library_id,borrow_type,borrow_time,due_time,return_time,borrow_status,renew_count,fine_amount)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15) RETURNING *
            """, borrow_id, request.reader_id, request.reader_home_campus_id, request.book_id,
                request.copy_id, request.copy_owner_site_id, request.checkout_library_id,
                request.return_library_id, request.borrow_type, request.borrow_time,
                request.due_time, request.return_time, request.borrow_status,
                request.renew_count, request.fine_amount)
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=400, detail=f"借阅记录新增失败：{exc}") from exc
    await _publish_change(request.query_id, "BORROW_CREATED", f"Site {site_id} 新增借阅记录 {borrow_id}。", {"borrow_id": borrow_id})
    return record_to_dict(record)


@app.patch("/internal/admin/borrow-records/{borrow_id}")
async def update_borrow(borrow_id: int, request: BorrowAdminUpdate, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    assignments=[]; values=[]
    for column,value in (("return_library_id",request.return_library_id),("due_time",request.due_time),("return_time",request.return_time),("borrow_status",request.borrow_status),("renew_count",request.renew_count),("fine_amount",request.fine_amount)):
        if value is not None: values.append(value); assignments.append(f"{column}=${len(values)}")
    if not assignments: raise HTTPException(status_code=400, detail="没有需要更新的借阅字段。")
    values.append(borrow_id)
    try:
        async with app.state.pool.acquire() as connection:
            record=await connection.fetchrow(f"UPDATE borrow_record_fragment SET {', '.join(assignments)}, updated_at=CURRENT_TIMESTAMP WHERE borrow_id=${len(values)} RETURNING *",*values)
    except asyncpg.PostgresError as exc: raise HTTPException(status_code=400, detail=f"借阅记录更新失败：{exc}") from exc
    if not record: raise HTTPException(status_code=404, detail="本站点不存在该借阅记录。")
    await _publish_change(request.query_id,"BORROW_UPDATED",f"Site {site_id} 更新借阅记录 {borrow_id}。",{"borrow_id":borrow_id})
    return record_to_dict(record)


@app.delete("/internal/admin/borrow-records/{borrow_id}")
async def delete_borrow(borrow_id: int, query_id: str, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    async with app.state.pool.acquire() as connection: record=await connection.fetchrow("DELETE FROM borrow_record_fragment WHERE borrow_id=$1 RETURNING borrow_id",borrow_id)
    if not record: raise HTTPException(status_code=404, detail="本站点不存在该借阅记录。")
    await _publish_change(query_id,"BORROW_DELETED",f"Site {site_id} 删除借阅记录 {borrow_id}。",{"borrow_id":borrow_id})
    return record_to_dict(record)


@app.post("/internal/admin/libraries")
async def create_library(request: LibraryAdminCreate, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    try:
        async with app.state.pool.acquire() as connection, connection.transaction():
            await connection.execute("LOCK TABLE library_fragment IN EXCLUSIVE MODE")
            base=site_id*1000
            library_id=await connection.fetchval("SELECT GREATEST(COALESCE(MAX(library_id),$1),$1)+1 FROM library_fragment",base)
            record=await connection.fetchrow("""INSERT INTO library_fragment (library_id,university_id,campus_id,library_name,address,longitude,latitude,location,open_time,close_time,phone,total_seats,service_radius_m,status) VALUES ($1,$2,$3,$4,$5,$6::numeric,$7::numeric,ST_SetSRID(ST_MakePoint($6::double precision,$7::double precision),4326)::geography,$8,$9,$10,$11,$12,$13) RETURNING *""",library_id,request.university_id,request.campus_id,request.library_name,request.address,request.longitude,request.latitude,request.open_time,request.close_time,request.phone,request.total_seats,request.service_radius_m,request.status)
    except asyncpg.PostgresError as exc: raise HTTPException(status_code=400, detail=f"图书馆新增失败：{exc}") from exc
    await _publish_change(request.query_id,"LIBRARY_CREATED",f"Site {site_id} 新增图书馆 {library_id}。",{"library_id":library_id})
    return record_to_dict(record)


@app.patch("/internal/admin/libraries/{library_id}")
async def update_library(library_id: int, request: LibraryAdminUpdate, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    fields=request.model_dump(exclude={"query_id"},exclude_none=True); longitude=fields.pop("longitude",None); latitude=fields.pop("latitude",None)
    async with app.state.pool.acquire() as connection:
        current=await connection.fetchrow("SELECT longitude,latitude FROM library_fragment WHERE library_id=$1",library_id)
        if not current: raise HTTPException(status_code=404,detail="本站点不存在该图书馆。")
        if longitude is not None or latitude is not None:
            fields["longitude"]=longitude if longitude is not None else current["longitude"]
            fields["latitude"]=latitude if latitude is not None else current["latitude"]
        values=[]; assignments=[]
        for column,value in fields.items():
            values.append(value)
            cast = "::numeric" if column in {"longitude", "latitude"} else ""
            assignments.append(f"{column}=${len(values)}{cast}")
        if "longitude" in fields:
            longitude_parameter = list(fields).index("longitude") + 1
            latitude_parameter = list(fields).index("latitude") + 1
            assignments.append(
                f"location=ST_SetSRID(ST_MakePoint(${longitude_parameter}::double precision,"
                f"${latitude_parameter}::double precision),4326)::geography"
            )
        if not assignments: raise HTTPException(status_code=400,detail="没有需要更新的图书馆字段。")
        values.append(library_id)
        record=await connection.fetchrow(f"UPDATE library_fragment SET {', '.join(assignments)},updated_at=CURRENT_TIMESTAMP WHERE library_id=${len(values)} RETURNING *",*values)
    await _publish_change(request.query_id,"LIBRARY_UPDATED",f"Site {site_id} 更新图书馆 {library_id}。",{"library_id":library_id})
    return record_to_dict(record)


@app.delete("/internal/admin/libraries/{library_id}")
async def delete_library(library_id: int, query_id: str, x_internal_token: str | None = Header(default=None)) -> dict[str, object]:
    _check_internal_token(x_internal_token)
    try:
        async with app.state.pool.acquire() as connection: record=await connection.fetchrow("DELETE FROM library_fragment WHERE library_id=$1 RETURNING library_id,library_name",library_id)
    except asyncpg.PostgresError as exc: raise HTTPException(status_code=409,detail=f"图书馆仍有关联馆藏，不能删除：{exc}") from exc
    if not record: raise HTTPException(status_code=404,detail="本站点不存在该图书馆。")
    await _publish_change(query_id,"LIBRARY_DELETED",f"Site {site_id} 删除图书馆 {library_id}。",{"library_id":library_id})
    return record_to_dict(record)


@app.get("/api/events")
async def recent_events() -> list[dict[str, object]]:
    return [event.model_dump(mode="json") for event in event_bus.recent()]


@app.websocket("/ws/events")
async def events_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = await event_bus.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        pass
    finally:
        await event_bus.unsubscribe(queue)
