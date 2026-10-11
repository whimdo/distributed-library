import pytest

from backend.coordinator.sql_parser import (
    QueryValidationError,
    parse_logical_query,
    parse_logical_write,
    render_physical_query,
)


def test_fragment_table_is_rewritten() -> None:
    parsed = parse_logical_query(
        "SELECT borrow_id, reader_id FROM borrow_record "
        "WHERE reader_id = 110000000001"
    )
    physical = render_physical_query(parsed)
    assert "borrow_record_fragment" in physical
    assert "LIMIT 500" in physical


def test_coordinator_join_is_allowed() -> None:
    parsed = parse_logical_query(
        "SELECT b.book_id, b.title, c.category_name "
        "FROM book b JOIN category c ON c.category_id = b.category_id"
    )
    physical = render_physical_query(parsed)
    assert "book_catalog" in physical
    assert "category" in physical


def test_mixed_location_join_is_rejected() -> None:
    with pytest.raises(QueryValidationError, match="暂不支持"):
        parse_logical_query(
            "SELECT b.title, c.copy_id "
            "FROM book b JOIN book_copy c ON c.book_id = b.book_id"
        )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM book",
        "SELECT * FROM book WHERE book_id IN (SELECT book_id FROM book)",
        "SELECT password_hash FROM reader",
        "SELECT * FROM pg_catalog.pg_tables",
    ],
)
def test_unsafe_queries_are_rejected(sql: str) -> None:
    with pytest.raises(QueryValidationError):
        parse_logical_query(sql)


def test_limit_is_capped() -> None:
    parsed = parse_logical_query("SELECT book_id FROM book LIMIT 99999", max_rows=200)
    assert parsed.limit == 200
    assert "LIMIT 200" in render_physical_query(parsed)


def test_postgis_output_function_is_allowed() -> None:
    parsed = parse_logical_query(
        "SELECT campus_id, ST_AsGeoJSON(boundary) AS boundary_geojson "
        "FROM campus WHERE campus_id = 1004"
    )
    physical = render_physical_query(parsed)
    assert "ST_ASGEOJSON" in physical.upper()


def test_reader_star_does_not_expose_password_hash() -> None:
    parsed = parse_logical_query("SELECT * FROM reader WHERE reader_id = 110000000001")
    physical = render_physical_query(parsed)
    assert "password_hash" not in physical
    assert "reader_name" in physical
    assert "*" not in physical


def test_insert_is_parsed_as_structured_command() -> None:
    parsed = parse_logical_write(
        "INSERT INTO reader (home_university_id, home_campus_id, student_no, "
        "network_card_no, reader_name, reader_type) VALUES "
        "(102, 1004, 'TEST-S001', 'CARD-001', '测试学生', 'UNDERGRADUATE')"
    )
    assert parsed.operation == "INSERT"
    assert parsed.logical_table == "reader"
    assert parsed.values["home_campus_id"] == 1004


def test_update_requires_primary_key_equality() -> None:
    with pytest.raises(QueryValidationError, match="reader_id"):
        parse_logical_write("UPDATE reader SET status='FROZEN' WHERE status='ACTIVE'")


def test_delete_without_where_is_rejected() -> None:
    with pytest.raises(QueryValidationError, match="主键等值"):
        parse_logical_write("DELETE FROM book_copy")


def test_write_rejects_system_and_routing_key_update() -> None:
    with pytest.raises(QueryValidationError):
        parse_logical_write(
            "UPDATE reader SET reader_id=210000000001 WHERE reader_id=110000000001"
        )
