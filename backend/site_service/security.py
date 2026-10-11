from __future__ import annotations

import sqlglot
from sqlglot import exp

from backend.coordinator.logical_catalog import PHYSICAL_FRAGMENT_TABLES


class PhysicalQueryValidationError(ValueError):
    pass


def validate_physical_query(sql: str) -> None:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise PhysicalQueryValidationError(f"物理 SQL 语法错误：{exc}") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise PhysicalQueryValidationError("分节点只接受一条 SELECT。")
    expression = statements[0]
    if expression.find(exp.Subquery) or expression.find(exp.CTE):
        raise PhysicalQueryValidationError("分节点不接受子查询或 CTE。")
    if expression.args.get("locks"):
        raise PhysicalQueryValidationError("分节点不接受行锁查询。")
    tables = {table.name.lower() for table in expression.find_all(exp.Table)}
    if not tables or not tables.issubset(PHYSICAL_FRAGMENT_TABLES):
        allowed = ", ".join(sorted(PHYSICAL_FRAGMENT_TABLES))
        raise PhysicalQueryValidationError(f"物理表不在白名单中：{allowed}。")
