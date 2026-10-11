from __future__ import annotations

from typing import Any

import asyncpg

from backend.coordinator.logical_catalog import LOGICAL_TABLES
from backend.coordinator.sql_parser import (
    ParsedQuery,
    QueryValidationError,
    equality_conditions,
)


def _site_from_prefixed_id(value: Any) -> int | None:
    text = str(value)
    if not text or text[0] not in {"1", "2", "3"}:
        return None
    return int(text[0])


def _candidate_tables(parsed: ParsedQuery, qualifier: str | None) -> list[str]:
    if qualifier:
        logical_name = parsed.aliases.get(qualifier.lower())
        return [logical_name] if logical_name else []
    return parsed.logical_tables


async def select_sites(
    parsed: ParsedQuery,
    coordinator_pool: asyncpg.Pool,
) -> tuple[list[int], str]:
    selected: set[int] = set()
    reasons: list[str] = []
    for qualifier, field, value in equality_conditions(parsed):
        for logical_name in _candidate_tables(parsed, qualifier):
            strategy = LOGICAL_TABLES[logical_name].routing_fields.get(field)
            if strategy == "id_prefix":
                site_id = _site_from_prefixed_id(value)
                if site_id:
                    selected.add(site_id)
                    reasons.append(f"{field} 的站点前缀为 {site_id}")
            elif strategy == "campus":
                try:
                    campus_id = int(value)
                except (TypeError, ValueError):
                    continue
                async with coordinator_pool.acquire() as connection:
                    site_id = await connection.fetchval(
                        "SELECT site_id FROM campus WHERE campus_id = $1",
                        campus_id,
                    )
                if site_id is None:
                    raise QueryValidationError(f"不存在 campus_id={campus_id}。")
                selected.add(int(site_id))
                reasons.append(f"campus_id={campus_id} 路由到 Site {site_id}")

    if len(selected) > 1:
        raise QueryValidationError(
            "查询条件推导出多个互相冲突的目标站点，请检查 ID 与校区条件。"
        )
    if selected:
        return sorted(selected), "；".join(dict.fromkeys(reasons))
    return [1, 2, 3], "未找到可用于精确路由的条件，广播到三个数据站点"
