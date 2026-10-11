import pytest

from backend.coordinator.router import select_sites
from backend.coordinator.sql_parser import parse_logical_query


@pytest.mark.asyncio
async def test_reader_prefix_routes_to_one_site() -> None:
    parsed = parse_logical_query(
        "SELECT borrow_id FROM borrow_record WHERE reader_id = 110000000001"
    )
    sites, reason = await select_sites(parsed, None)  # type: ignore[arg-type]
    assert sites == [1]
    assert "前缀" in reason


@pytest.mark.asyncio
async def test_missing_route_broadcasts() -> None:
    parsed = parse_logical_query(
        "SELECT copy_id FROM book_copy WHERE copy_status = 'AVAILABLE'"
    )
    sites, reason = await select_sites(parsed, None)  # type: ignore[arg-type]
    assert sites == [1, 2, 3]
    assert "广播" in reason
