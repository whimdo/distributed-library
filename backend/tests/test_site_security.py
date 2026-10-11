import pytest

from backend.site_service.security import (
    PhysicalQueryValidationError,
    validate_physical_query,
)


def test_fragment_select_is_allowed() -> None:
    validate_physical_query(
        "SELECT copy_id FROM book_copy_fragment WHERE copy_status = 'AVAILABLE' LIMIT 20"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM book_copy_fragment",
        "SELECT * FROM book_catalog",
        "SELECT * FROM pg_catalog.pg_tables",
    ],
)
def test_non_fragment_query_is_rejected(sql: str) -> None:
    with pytest.raises(PhysicalQueryValidationError):
        validate_physical_query(sql)
