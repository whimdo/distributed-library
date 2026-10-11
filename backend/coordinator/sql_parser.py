from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sqlglot
from sqlglot import exp

from backend.coordinator.logical_catalog import LOGICAL_TABLES


class QueryValidationError(ValueError):
    pass


@dataclass(frozen=True)
class OrderSpec:
    output_key: str
    descending: bool


@dataclass(frozen=True)
class AggregateSpec:
    function: str
    output_key: str
    distinct: bool


@dataclass
class ParsedQuery:
    original_sql: str
    expression: exp.Select
    logical_tables: list[str]
    aliases: dict[str, str]
    limit: int
    order_by: list[OrderSpec]
    aggregates: list[AggregateSpec]

    @property
    def location(self) -> str:
        locations = {LOGICAL_TABLES[name].location for name in self.logical_tables}
        if len(locations) != 1:
            return "mixed"
        return next(iter(locations))


@dataclass(frozen=True)
class ParsedWrite:
    original_sql: str
    operation: str
    logical_table: str
    values: dict[str, Any]
    key_field: str | None = None
    key_value: Any | None = None


WRITE_PRIMARY_KEYS = {
    "reader": "reader_id",
    "book_copy": "copy_id",
    "borrow_record": "borrow_id",
    "library": "library_id",
}


ALLOWED_FUNCTIONS = {
    "AVG", "CAST", "COALESCE", "COUNT", "LENGTH", "LOWER", "MAX", "MIN", "SUM",
    "UPPER", "ST_ASGEOJSON", "ST_ASTEXT", "ST_DISTANCE", "ST_DWITHIN",
}

FORBIDDEN_NODES = (
    exp.CTE,
    exp.Except,
    exp.Intersect,
    exp.Into,
    exp.Subquery,
    exp.Union,
)


def _literal_value(node: exp.Expression) -> Any | None:
    if not isinstance(node, exp.Literal):
        return None
    if node.is_string:
        return node.this
    text = str(node.this)
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return None


def _write_literal(node: exp.Expression) -> Any:
    if isinstance(node, exp.Boolean):
        return bool(node.this)
    if isinstance(node, exp.Null):
        return None
    if isinstance(node, exp.Neg) and isinstance(node.this, exp.Literal):
        value = _literal_value(node.this)
        if isinstance(value, (int, float)):
            return -value
    if isinstance(node, exp.Literal):
        return _literal_value(node)
    raise QueryValidationError("写操作的值只允许字符串、数字、布尔值或 NULL 常量。")


def _write_table(node: exp.Expression) -> str:
    if not isinstance(node, exp.Table) or node.catalog or node.db:
        raise QueryValidationError("写操作必须直接指定一个逻辑表，不能指定 schema。")
    name = node.name.lower()
    if name not in WRITE_PRIMARY_KEYS:
        allowed = ", ".join(WRITE_PRIMARY_KEYS)
        raise QueryValidationError(f"当前写操作仅支持逻辑表：{allowed}。")
    return name


def _validate_write_columns(table: str, values: dict[str, Any]) -> None:
    unknown = set(values) - LOGICAL_TABLES[table].columns
    if unknown:
        raise QueryValidationError(f"逻辑表 {table!r} 不存在字段：{', '.join(sorted(unknown))}。")
    protected = {WRITE_PRIMARY_KEYS[table], "created_at", "updated_at", "current_borrow_count"}
    forbidden = set(values) & protected
    if forbidden:
        raise QueryValidationError(f"不允许直接写入系统字段：{', '.join(sorted(forbidden))}。")


def _primary_key_condition(expression: exp.Expression, table: str) -> tuple[str, Any]:
    where = expression.args.get("where")
    condition = where.this if isinstance(where, exp.Where) else None
    if not isinstance(condition, exp.EQ):
        raise QueryValidationError("UPDATE/DELETE 必须使用主键等值 WHERE 条件。")
    left, right = condition.this, condition.expression
    if isinstance(right, exp.Column):
        left, right = right, left
    key = WRITE_PRIMARY_KEYS[table]
    if not isinstance(left, exp.Column) or left.name.lower() != key:
        raise QueryValidationError(f"{table} 的写操作必须使用 WHERE {key} = 常量。")
    value = _write_literal(right)
    if not isinstance(value, int):
        raise QueryValidationError(f"{key} 必须是整数。")
    return key, value


def parse_logical_write(sql: str) -> ParsedWrite:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise QueryValidationError(f"SQL 语法错误：{exc}") from exc
    if len(statements) != 1:
        raise QueryValidationError("一次只能执行一条 SQL。")
    expression = statements[0]
    if isinstance(expression, exp.Insert):
        if not isinstance(expression.this, exp.Schema):
            raise QueryValidationError("INSERT 必须显式列出字段。")
        table = _write_table(expression.this.this)
        columns = [identifier.name.lower() for identifier in expression.this.expressions]
        source = expression.expression
        if not isinstance(source, exp.Values) or len(source.expressions) != 1:
            raise QueryValidationError("INSERT 仅支持一行 VALUES，不支持 SELECT 或批量插入。")
        tuple_node = source.expressions[0]
        if not isinstance(tuple_node, exp.Tuple) or len(columns) != len(tuple_node.expressions):
            raise QueryValidationError("INSERT 字段数量与 VALUES 数量不一致。")
        if len(columns) != len(set(columns)):
            raise QueryValidationError("INSERT 不能重复指定字段。")
        values = dict(zip(columns, (_write_literal(value) for value in tuple_node.expressions)))
        _validate_write_columns(table, values)
        return ParsedWrite(sql, "INSERT", table, values)
    if isinstance(expression, exp.Update):
        table = _write_table(expression.this)
        values: dict[str, Any] = {}
        for assignment in expression.expressions:
            if not isinstance(assignment, exp.EQ) or not isinstance(assignment.this, exp.Column):
                raise QueryValidationError("UPDATE SET 仅支持字段 = 常量。")
            values[assignment.this.name.lower()] = _write_literal(assignment.expression)
        if not values:
            raise QueryValidationError("UPDATE 至少需要修改一个字段。")
        _validate_write_columns(table, values)
        key_field, key_value = _primary_key_condition(expression, table)
        return ParsedWrite(sql, "UPDATE", table, values, key_field, key_value)
    if isinstance(expression, exp.Delete):
        table = _write_table(expression.this)
        key_field, key_value = _primary_key_condition(expression, table)
        return ParsedWrite(sql, "DELETE", table, {}, key_field, key_value)
    raise QueryValidationError("写入解析器只接受 INSERT、UPDATE 或 DELETE。")


def statement_type(sql: str) -> str:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise QueryValidationError(f"SQL 语法错误：{exc}") from exc
    if len(statements) != 1:
        raise QueryValidationError("一次只能执行一条 SQL。")
    expression = statements[0]
    if isinstance(expression, exp.Select):
        return "SELECT"
    if isinstance(expression, (exp.Insert, exp.Update, exp.Delete)):
        return expression.key.upper()
    raise QueryValidationError("仅支持 SELECT、INSERT、UPDATE 和 DELETE。")


def equality_conditions(parsed: ParsedQuery) -> list[tuple[str | None, str, Any]]:
    conditions: list[tuple[str | None, str, Any]] = []
    for equality in parsed.expression.find_all(exp.EQ):
        left, right = equality.this, equality.expression
        if isinstance(left, exp.Column):
            value = _literal_value(right)
            if value is not None:
                conditions.append((left.table or None, left.name.lower(), value))
        if isinstance(right, exp.Column):
            value = _literal_value(left)
            if value is not None:
                conditions.append((right.table or None, right.name.lower(), value))
    return conditions


def _table_and_aliases(expression: exp.Select) -> tuple[list[str], dict[str, str]]:
    logical_tables: list[str] = []
    aliases: dict[str, str] = {}
    for table in expression.find_all(exp.Table):
        if table.catalog or table.db:
            raise QueryValidationError("不允许指定数据库名或 schema 名。")
        name = table.name.lower()
        if name not in LOGICAL_TABLES:
            allowed = ", ".join(LOGICAL_TABLES)
            raise QueryValidationError(f"未知逻辑表 {name!r}；允许的表：{allowed}。")
        if name not in logical_tables:
            logical_tables.append(name)
        aliases[name] = name
        if table.alias:
            aliases[table.alias.lower()] = name
    if not logical_tables:
        raise QueryValidationError("SELECT 必须包含 FROM 逻辑表。")
    return logical_tables, aliases


def _validate_columns(
    expression: exp.Select,
    logical_tables: list[str],
    aliases: dict[str, str],
) -> None:
    for column in expression.find_all(exp.Column):
        name = column.name.lower()
        if name == "*":
            continue
        if column.table:
            qualifier = column.table.lower()
            logical_name = aliases.get(qualifier)
            if logical_name is None:
                raise QueryValidationError(f"未知表或别名 {column.table!r}。")
            if name not in LOGICAL_TABLES[logical_name].columns:
                raise QueryValidationError(
                    f"逻辑表 {logical_name!r} 中不存在字段 {column.name!r}。"
                )
            continue
        matches = [
            table_name
            for table_name in logical_tables
            if name in LOGICAL_TABLES[table_name].columns
        ]
        if not matches:
            raise QueryValidationError(f"查询中不存在可用字段 {column.name!r}。")
        if len(matches) > 1 and len(logical_tables) > 1:
            raise QueryValidationError(
                f"字段 {column.name!r} 在多个表中存在，请添加表名或别名。"
            )


def _read_limit(expression: exp.Select, max_rows: int) -> int:
    limit_node = expression.args.get("limit")
    if limit_node is None:
        limit = max_rows
    else:
        value = _literal_value(limit_node.expression)
        if not isinstance(value, int) or value <= 0:
            raise QueryValidationError("LIMIT 必须是正整数。")
        limit = min(value, max_rows)
    expression.set("limit", exp.Limit(expression=exp.Literal.number(limit)))
    return limit


def _read_order(expression: exp.Select) -> list[OrderSpec]:
    order_node = expression.args.get("order")
    if order_node is None:
        return []
    specs: list[OrderSpec] = []
    for ordered in order_node.expressions:
        target = ordered.this
        if not isinstance(target, exp.Column):
            raise QueryValidationError("分布式查询的 ORDER BY 仅支持字段或字段别名。")
        specs.append(
            OrderSpec(
                output_key=target.name,
                descending=bool(ordered.args.get("desc")),
            )
        )
    return specs


def _read_aggregates(expression: exp.Select) -> list[AggregateSpec]:
    specs: list[AggregateSpec] = []
    for selected in expression.expressions:
        output_key = selected.alias_or_name
        inner = selected.this if isinstance(selected, exp.Alias) else selected
        if isinstance(inner, exp.AggFunc):
            specs.append(
                AggregateSpec(
                    function=inner.sql_name().upper(),
                    output_key=output_key or inner.sql_name().lower(),
                    distinct=inner.find(exp.Distinct) is not None,
                )
            )
    return specs


def parse_logical_query(sql: str, max_rows: int = 500) -> ParsedQuery:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise QueryValidationError(f"SQL 语法错误：{exc}") from exc
    if len(statements) != 1:
        raise QueryValidationError("一次只能执行一条 SQL。")
    expression = statements[0]
    if not isinstance(expression, exp.Select):
        raise QueryValidationError("查询界面只允许执行 SELECT。")
    for node_type in FORBIDDEN_NODES:
        if expression.find(node_type):
            raise QueryValidationError("当前版本不支持子查询、CTE 或集合运算。")
    if expression.args.get("locks"):
        raise QueryValidationError("不允许 SELECT FOR UPDATE/SHARE。")

    logical_tables, aliases = _table_and_aliases(expression)
    if len(logical_tables) > 1 and any(
        isinstance(selected, exp.Star) for selected in expression.expressions
    ):
        raise QueryValidationError("多表查询使用 * 时必须写成表别名.*。")
    locations = {LOGICAL_TABLES[name].location for name in logical_tables}
    if len(locations) > 1:
        raise QueryValidationError(
            "当前版本暂不支持主节点逻辑表与分片逻辑表直接 JOIN；请拆成两条查询。"
        )
    _validate_columns(expression, logical_tables, aliases)

    for function in expression.find_all(exp.Func):
        name = (
            function.name.upper()
            if isinstance(function, exp.Anonymous)
            else function.sql_name().upper()
        )
        if name not in ALLOWED_FUNCTIONS:
            raise QueryValidationError(f"当前版本不允许函数 {name}。")

    if expression.args.get("offset"):
        raise QueryValidationError("当前版本暂不支持 OFFSET。")

    limit = _read_limit(expression, max_rows)
    order_by = _read_order(expression)
    aggregates = _read_aggregates(expression)
    return ParsedQuery(
        original_sql=sql,
        expression=expression,
        logical_tables=logical_tables,
        aliases=aliases,
        limit=limit,
        order_by=order_by,
        aggregates=aggregates,
    )


def render_physical_query(parsed: ParsedQuery) -> str:
    expression = parsed.expression.copy()
    expanded_select: list[exp.Expression] = []
    for selected in expression.expressions:
        if isinstance(selected, exp.Star):
            logical_name = parsed.logical_tables[0]
            expanded_select.extend(
                exp.column(column_name)
                for column_name in sorted(LOGICAL_TABLES[logical_name].columns)
            )
            continue
        if isinstance(selected, exp.Column) and isinstance(selected.this, exp.Star):
            qualifier = selected.table.lower()
            logical_name = parsed.aliases[qualifier]
            expanded_select.extend(
                exp.column(column_name, table=selected.table)
                for column_name in sorted(LOGICAL_TABLES[logical_name].columns)
            )
            continue
        expanded_select.append(selected)
    expression.set("expressions", expanded_select)
    for table in expression.find_all(exp.Table):
        logical_name = table.name.lower()
        physical_name = LOGICAL_TABLES[logical_name].physical_name
        table.set("this", exp.to_identifier(physical_name))
    return expression.sql(dialect="postgres")
