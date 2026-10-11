from __future__ import annotations

from contextlib import asynccontextmanager

import asyncpg
import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.common.config import get_settings
from backend.common.event_bus import EventBus
from backend.common.models import AuthUser, LoginRequest, LoginResponse, QueryRequest, QueryResponse
from backend.coordinator.admin_api import router as admin_router
from backend.coordinator.auth import (
    AdminUser,
    AuthenticatedUser,
    GlobalAdminUser,
    create_access_token,
    verify_password,
)
from backend.coordinator.logical_catalog import LOGICAL_TABLES
from backend.coordinator.query_engine import execute_query
from backend.coordinator.site_client import SiteClient, SiteExecutionError
from backend.coordinator.sql_parser import QueryValidationError
from backend.coordinator.sql_parser import statement_type
from backend.coordinator.write_engine import execute_write
from backend.coordinator.public_api import router as public_router


settings = get_settings()
event_bus = EventBus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.coordinator_pool = await asyncpg.create_pool(
        dsn=settings.coordinator_database_url,
        min_size=1,
        max_size=5,
        command_timeout=settings.query_timeout_seconds,
    )
    app.state.http_client = httpx.AsyncClient(
        timeout=settings.query_timeout_seconds + 2,
    )
    app.state.site_client = SiteClient(
        app.state.http_client,
        settings.site_api_urls,
        settings.internal_api_token,
        event_bus,
    )
    yield
    await app.state.http_client.aclose()
    await app.state.coordinator_pool.close()


app = FastAPI(
    title="Distributed Library Coordinator",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)
app.include_router(admin_router)
app.include_router(public_router)


@app.exception_handler(SiteExecutionError)
async def site_execution_error_handler(request: Request, exc: SiteExecutionError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
async def health() -> dict[str, object]:
    async with app.state.coordinator_pool.acquire() as connection:
        database = await connection.fetchval("SELECT current_database()")
    return {"service": "coordinator", "database": database, "status": "healthy"}


@app.get("/api/logical-schema")
async def logical_schema(user: GlobalAdminUser) -> dict[str, object]:
    return {
        "tables": [
            {
                "logical_name": table.logical_name,
                "location": table.location,
                "columns": sorted(table.columns),
            }
            for table in LOGICAL_TABLES.values()
        ]
    }


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, user: GlobalAdminUser) -> QueryResponse:
    try:
        if statement_type(request.sql) != "SELECT":
            return await execute_write(
                request.sql,
                user,
                app.state.coordinator_pool,
                app.state.site_client,
                event_bus,
            )
        return await execute_query(
            request.sql,
            app.state.coordinator_pool,
            app.state.site_client,
            event_bus,
            settings.max_result_rows,
        )
    except QueryValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SiteExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=400, detail=f"数据库执行失败：{exc}") from exc


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    record = await app.state.coordinator_pool.fetchrow("""
        SELECT account_id, username, password_hash, display_name, role,
               reader_id, home_site_id, managed_site_id, account_status
        FROM user_account WHERE username = $1
    """, request.username.strip())
    if (
        record is None
        or record["account_status"] != "ACTIVE"
        or not verify_password(request.password, record["password_hash"])
    ):
        raise HTTPException(status_code=401, detail="账号或密码错误。")
    user = AuthUser(
        account_id=record["account_id"],
        username=record["username"],
        display_name=record["display_name"],
        role=record["role"],
        reader_id=record["reader_id"],
        home_site_id=record["home_site_id"],
        managed_site_id=record["managed_site_id"],
    )
    await app.state.coordinator_pool.execute(
        "UPDATE user_account SET last_login_at = CURRENT_TIMESTAMP WHERE account_id = $1",
        user.account_id,
    )
    return LoginResponse(access_token=create_access_token(user), user=user)


@app.get("/api/auth/me", response_model=AuthUser)
async def me(user: AuthenticatedUser) -> AuthUser:
    return user


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
