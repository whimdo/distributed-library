from __future__ import annotations

from numbers import Number
from uuid import uuid4

import asyncpg

from backend.common.event_bus import EventBus
from backend.common.models import (
    PhysicalQueryInfo,
    QueryResponse,
    SiteExecuteRequest,
    SiteExecuteResponse,
)
from backend.common.serialization import record_to_dict
from backend.coordinator.router import select_sites
from backend.coordinator.site_client import SiteClient
from backend.coordinator.sql_parser import (
    AggregateSpec,
    ParsedQuery,
    QueryValidationError,
    parse_logical_query,
    render_physical_query,
)


def _merge_aggregates(
    parsed: ParsedQuery,
    results: list[SiteExecuteResponse],
) -> list[dict[str, object]]:
    if parsed.expression.args.get("group") or parsed.expression.args.get("having"):
        raise QueryValidationError("广播查询暂不支持 GROUP BY 或 HAVING。")
    if len(parsed.aggregates) != len(parsed.expression.expressions):
        raise QueryValidationError("广播聚合查询不能同时选择普通字段。")
    if not parsed.aggregates:
        return []
    unsupported = {
        aggregate.function
        for aggregate in parsed.aggregates
        if aggregate.function not in {"COUNT", "SUM", "MIN", "MAX"}
        or aggregate.distinct
    }
    if unsupported:
        names = ", ".join(sorted(unsupported)) or "DISTINCT"
        raise QueryValidationError(
            f"广播查询暂不支持聚合 {names}；可使用 COUNT、SUM、MIN、MAX。"
        )

    merged: dict[str, object] = {}
    for aggregate in parsed.aggregates:
        values = [
            result.rows[0].get(aggregate.output_key)
            for result in results
            if result.rows
        ]
        values = [value for value in values if value is not None]
        if aggregate.function in {"COUNT", "SUM"}:
            if not all(isinstance(value, Number) for value in values):
                raise QueryValidationError(
                    f"无法合并聚合字段 {aggregate.output_key!r}。"
                )
            merged[aggregate.output_key] = sum(values)
        elif aggregate.function == "MIN":
            merged[aggregate.output_key] = min(values) if values else None
        elif aggregate.function == "MAX":
            merged[aggregate.output_key] = max(values) if values else None
    return [merged]


def _sort_rows(parsed: ParsedQuery, rows: list[dict[str, object]]) -> None:
    for order in reversed(parsed.order_by):
        if rows and order.output_key not in rows[0]:
            raise QueryValidationError(
                f"ORDER BY 字段 {order.output_key!r} 不在查询输出中。"
            )
        rows.sort(
            key=lambda row: (row.get(order.output_key) is None, row.get(order.output_key)),
            reverse=order.descending,
        )


async def execute_query(
    sql: str,
    coordinator_pool: asyncpg.Pool,
    site_client: SiteClient,
    event_bus: EventBus,
    max_rows: int,
) -> QueryResponse:
    query_id = uuid4().hex
    await event_bus.publish(
        query_id,
        "coordinator",
        "COMMAND_RECEIVED",
        "收到用户逻辑 SQL。",
        {"sql": sql},
    )
    parsed = parse_logical_query(sql, max_rows=max_rows)
    await event_bus.publish(
        query_id,
        "coordinator",
        "SQL_PARSED",
        "SQL 解析与安全校验通过。",
        {"logical_tables": parsed.logical_tables},
    )
    physical_sql = render_physical_query(parsed)
    await event_bus.publish(
        query_id,
        "coordinator",
        "PHYSICAL_SQL_CREATED",
        "逻辑表已改写为物理表。",
        {"sql": physical_sql},
    )

    selected_sites: list[int] = []
    physical_queries: list[PhysicalQueryInfo] = []
    rows: list[dict[str, object]] = []
    columns: list[str] = []

    if parsed.location == "coordinator":
        physical_queries.append(
            PhysicalQueryInfo(target="coordinator_db", sql=physical_sql)
        )
        await event_bus.publish(
            query_id,
            "coordinator",
            "LOCAL_SQL_EXECUTING",
            "在主节点数据库执行物理 SQL。",
            {"sql": physical_sql},
        )
        async with coordinator_pool.acquire() as connection:
            records = await connection.fetch(physical_sql)
        rows = [record_to_dict(record) for record in records]
        columns = list(records[0].keys()) if records else []
    else:
        selected_sites, reason = await select_sites(parsed, coordinator_pool)
        await event_bus.publish(
            query_id,
            "coordinator",
            "SITE_SELECTED",
            reason,
            {
                "selected_sites": selected_sites,
                "pruned_sites": [site for site in (1, 2, 3) if site not in selected_sites],
            },
        )
        request = SiteExecuteRequest(
            query_id=query_id,
            sql=physical_sql,
            logical_tables=parsed.logical_tables,
        )
        results = await site_client.execute_many(selected_sites, request)
        physical_queries.extend(
            PhysicalQueryInfo(target=f"site{site_id}_db", sql=physical_sql)
            for site_id in selected_sites
        )
        if len(selected_sites) > 1 and parsed.aggregates:
            rows = _merge_aggregates(parsed, results)
        else:
            rows = [row for result in results for row in result.rows]
            if len(selected_sites) > 1 and parsed.order_by:
                _sort_rows(parsed, rows)
            rows = rows[: parsed.limit]
        if rows:
            columns = list(rows[0].keys())
        elif results:
            columns = results[0].columns

    await event_bus.publish(
        query_id,
        "coordinator",
        "RESULT_MERGED",
        f"查询结果已合并，共 {len(rows)} 行。",
        {"row_count": len(rows)},
    )
    await event_bus.publish(
        query_id,
        "coordinator",
        "QUERY_COMPLETED",
        "查询执行完成。",
    )
    return QueryResponse(
        query_id=query_id,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        selected_sites=selected_sites,
        physical_queries=physical_queries,
        events=event_bus.for_query(query_id),
    )
