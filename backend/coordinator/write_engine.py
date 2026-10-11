from __future__ import annotations

from uuid import uuid4

import asyncpg
from pydantic import ValidationError

from backend.common.event_bus import EventBus
from backend.common.models import (
    AuthUser, BorrowAdminCreate, BorrowAdminUpdate, CopyAdminCreate,
    CopyAdminUpdate, LibraryAdminCreate, LibraryAdminUpdate,
    PhysicalQueryInfo, QueryResponse, ReaderAdminCreate, ReaderAdminUpdate,
)
from backend.coordinator.logical_catalog import LOGICAL_TABLES
from backend.coordinator.site_client import SiteClient
from backend.coordinator.sql_parser import ParsedWrite, QueryValidationError, parse_logical_write


STUDENT_DEMO_PASSWORD_HASH = "pbkdf2_sha256$210000$student-demo-salt$Vh9SOj2IZ6AA43tz6O76usw_VEjtqC4BwyNb63hEF6k"
RESOURCE_PATHS = {"reader": "readers", "book_copy": "copies", "borrow_record": "borrow-records", "library": "libraries"}
CREATE_MODELS = {"reader": ReaderAdminCreate, "book_copy": CopyAdminCreate, "borrow_record": BorrowAdminCreate, "library": LibraryAdminCreate}
UPDATE_MODELS = {"reader": ReaderAdminUpdate, "book_copy": CopyAdminUpdate, "borrow_record": BorrowAdminUpdate, "library": LibraryAdminUpdate}
ROUTING_FIELDS = {"reader": "home_campus_id", "book_copy": "owner_campus_id", "borrow_record": "reader_id", "library": "campus_id"}


def _site_from_id(value: object) -> int:
    text = str(value)
    if not text or text[0] not in {"1", "2", "3"}:
        raise QueryValidationError("主键没有有效的 Site 1/2/3 前缀，无法路由写操作。")
    return int(text[0])


async def _site_for_insert(parsed: ParsedWrite, pool: asyncpg.Pool) -> int:
    field = ROUTING_FIELDS[parsed.logical_table]
    if field not in parsed.values:
        raise QueryValidationError(f"INSERT {parsed.logical_table} 必须提供路由字段 {field}。")
    if field == "reader_id":
        return _site_from_id(parsed.values[field])
    campus_id = parsed.values[field]
    if not isinstance(campus_id, int):
        raise QueryValidationError(f"{field} 必须是整数。")
    site_id = await pool.fetchval("SELECT site_id FROM campus WHERE campus_id=$1 AND status='ACTIVE'", campus_id)
    if site_id is None:
        raise QueryValidationError(f"不存在可用的 campus_id={campus_id}。")
    return int(site_id)


def _validate_scope(user: AuthUser, site_id: int) -> None:
    if user.role == "SITE_ADMIN" and user.managed_site_id != site_id:
        raise QueryValidationError("站点管理员不能写入其他数据站点。")


async def _validate_relations(parsed: ParsedWrite, site_id: int, pool: asyncpg.Pool) -> None:
    values = parsed.values
    if parsed.operation == "INSERT" and parsed.logical_table in {"reader", "book_copy", "library"}:
        campus_field = "home_campus_id" if parsed.logical_table == "reader" else "owner_campus_id" if parsed.logical_table == "book_copy" else "campus_id"
        university_field = "home_university_id" if parsed.logical_table == "reader" else "owner_university_id" if parsed.logical_table == "book_copy" else "university_id"
        valid = await pool.fetchval(
            "SELECT EXISTS(SELECT 1 FROM campus WHERE campus_id=$1 AND university_id=$2 AND site_id=$3 AND status='ACTIVE')",
            values.get(campus_field), values.get(university_field), site_id,
        )
        if not valid:
            raise QueryValidationError("高校、校区与目标站点的归属关系不匹配。")
    if parsed.operation == "INSERT" and parsed.logical_table in {"book_copy", "borrow_record"}:
        exists = await pool.fetchval("SELECT EXISTS(SELECT 1 FROM book_catalog WHERE book_id=$1)", values.get("book_id"))
        if not exists:
            raise QueryValidationError(f"不存在 book_id={values.get('book_id')}。")


def _model_payload(parsed: ParsedWrite, query_id: str) -> dict[str, object]:
    model_class = CREATE_MODELS[parsed.logical_table] if parsed.operation == "INSERT" else UPDATE_MODELS[parsed.logical_table]
    allowed = set(model_class.model_fields) - {"query_id"}
    unsupported = set(parsed.values) - allowed
    if unsupported:
        raise QueryValidationError(f"{parsed.operation} {parsed.logical_table} 不允许字段：{', '.join(sorted(unsupported))}。")
    if parsed.operation == "UPDATE" and any(value is None for value in parsed.values.values()):
        raise QueryValidationError("当前版本的 UPDATE 暂不支持把字段设置为 NULL。")
    try:
        model = model_class(query_id=query_id, **parsed.values)
    except ValidationError as exc:
        messages = "; ".join(error["msg"] for error in exc.errors())
        raise QueryValidationError(f"写入字段校验失败：{messages}") from exc
    return model.model_dump(mode="json", exclude_none=True)


def _physical_sql(parsed: ParsedWrite) -> str:
    physical = LOGICAL_TABLES[parsed.logical_table].physical_name
    if parsed.operation == "INSERT":
        columns = list(parsed.values)
        placeholders = ", ".join(f"${index}" for index in range(1, len(columns) + 1))
        return f"INSERT INTO {physical} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING *"
    if parsed.operation == "UPDATE":
        assignments = ", ".join(f"{column} = ${index}" for index, column in enumerate(parsed.values, 1))
        return f"UPDATE {physical} SET {assignments} WHERE {parsed.key_field} = ${len(parsed.values)+1} RETURNING *"
    return f"DELETE FROM {physical} WHERE {parsed.key_field} = $1 RETURNING *"


async def execute_write(
    sql: str, user: AuthUser, pool: asyncpg.Pool, site_client: SiteClient, event_bus: EventBus,
) -> QueryResponse:
    query_id = uuid4().hex
    await event_bus.publish(query_id, "coordinator", "COMMAND_RECEIVED", "收到用户逻辑写入 SQL。", {"sql": sql})
    parsed = parse_logical_write(sql)
    await event_bus.publish(query_id, "coordinator", "WRITE_SQL_PARSED", f"识别为 {parsed.operation} {parsed.logical_table}，已转换为结构化命令。", {"operation": parsed.operation, "logical_table": parsed.logical_table, "values": parsed.values})
    site_id = await _site_for_insert(parsed, pool) if parsed.operation == "INSERT" else _site_from_id(parsed.key_value)
    _validate_scope(user, site_id)
    await _validate_relations(parsed, site_id, pool)
    await event_bus.publish(query_id, "coordinator", "WRITE_SITE_SELECTED", f"根据分片键将写操作路由到 Site {site_id}。", {"selected_sites": [site_id]})
    payload = _model_payload(parsed, query_id) if parsed.operation != "DELETE" else {}
    physical_sql = _physical_sql(parsed)
    await event_bus.publish(query_id, "coordinator", "PARAMETERIZED_SQL_CREATED", "已生成参数化物理 SQL；用户常量不会直接拼接执行。", {"sql": physical_sql})
    path = RESOURCE_PATHS[parsed.logical_table]
    if parsed.operation == "INSERT":
        result = await site_client.create_resource(site_id, path, payload)
        if parsed.logical_table == "reader":
            try:
                await pool.execute("""
                    INSERT INTO user_account (username,password_hash,display_name,role,reader_id,home_site_id,account_status)
                    VALUES ($1,$2,$3,'STUDENT',$4,$5,'ACTIVE')
                """, parsed.values["student_no"], STUDENT_DEMO_PASSWORD_HASH,
                    parsed.values["reader_name"], result["reader_id"], site_id)
            except Exception:
                await site_client.delete_resource(site_id, f"{path}/{result['reader_id']}", query_id)
                raise
    elif parsed.operation == "UPDATE":
        result = await site_client.update_resource(site_id, f"{path}/{parsed.key_value}", payload)
    else:
        result = await site_client.delete_resource(site_id, f"{path}/{parsed.key_value}", query_id)
        if parsed.logical_table == "reader":
            await pool.execute("DELETE FROM user_account WHERE reader_id=$1", parsed.key_value)
    await event_bus.publish(query_id, "coordinator", "WRITE_COMPLETED", f"{parsed.operation} 执行成功，影响 1 行。", {"affected_rows": 1})
    return QueryResponse(query_id=query_id, columns=list(result), rows=[result], row_count=1,
                         selected_sites=[site_id],
                         physical_queries=[PhysicalQueryInfo(target=f"site{site_id}_db", sql=physical_sql)],
                         events=event_bus.for_query(query_id))
