from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LogicalTable:
    logical_name: str
    physical_name: str
    location: str
    columns: frozenset[str]
    routing_fields: dict[str, str]


def _columns(*names: str) -> frozenset[str]:
    return frozenset(names)


LOGICAL_TABLES: dict[str, LogicalTable] = {
    "site": LogicalTable(
        "site",
        "site_node",
        "coordinator",
        _columns(
            "site_id", "site_name", "service_url", "database_host",
            "database_port", "database_name", "region_name",
            "region_geometry", "site_status", "last_heartbeat",
            "created_at", "updated_at",
        ),
        {},
    ),
    "university": LogicalTable(
        "university",
        "university",
        "coordinator",
        _columns(
            "university_id", "university_name", "short_name", "address",
            "website", "phone", "status", "created_at", "updated_at",
        ),
        {},
    ),
    "campus": LogicalTable(
        "campus",
        "campus",
        "coordinator",
        _columns(
            "campus_id", "university_id", "campus_name", "address",
            "longitude", "latitude", "center_location", "boundary",
            "site_id", "status", "created_at", "updated_at",
        ),
        {},
    ),
    "category": LogicalTable(
        "category",
        "category",
        "coordinator",
        _columns(
            "category_id", "category_name", "parent_id", "description",
            "sort_order", "status",
        ),
        {},
    ),
    "book": LogicalTable(
        "book",
        "book_catalog",
        "coordinator",
        _columns(
            "book_id", "isbn", "title", "author", "translator",
            "publisher", "publish_year", "edition", "category_id",
            "language", "page_count", "summary", "keywords", "cover_url",
            "created_at", "updated_at",
        ),
        {},
    ),
    "library": LogicalTable(
        "library",
        "library_fragment",
        "fragmented",
        _columns(
            "library_id", "university_id", "campus_id", "library_name",
            "address", "longitude", "latitude", "location", "open_time",
            "close_time", "phone", "total_seats", "status", "created_at",
            "updated_at", "service_radius_m",
        ),
        {"library_id": "id_prefix", "campus_id": "campus"},
    ),
    "reader": LogicalTable(
        "reader",
        "reader_fragment",
        "fragmented",
        _columns(
            "reader_id", "home_university_id", "home_campus_id",
            "student_no", "network_card_no", "reader_name", "phone",
            "email", "reader_type", "network_permission",
            "max_borrow_count", "current_borrow_count", "status",
            "created_at", "updated_at",
        ),
        {"reader_id": "id_prefix", "home_campus_id": "campus"},
    ),
    "book_copy": LogicalTable(
        "book_copy",
        "book_copy_fragment",
        "fragmented",
        _columns(
            "copy_id", "book_id", "owner_university_id", "owner_campus_id",
            "owner_library_id", "current_library_id", "barcode",
            "shelf_location", "copy_status", "allow_cross_borrow",
            "acquisition_date", "price", "created_at", "updated_at",
        ),
        {
            "copy_id": "id_prefix",
            "owner_library_id": "id_prefix",
            "owner_campus_id": "campus",
        },
    ),
    "borrow_record": LogicalTable(
        "borrow_record",
        "borrow_record_fragment",
        "fragmented",
        _columns(
            "borrow_id", "reader_id", "reader_home_campus_id", "book_id",
            "copy_id", "copy_owner_site_id", "checkout_library_id",
            "return_library_id", "borrow_type", "borrow_time", "due_time",
            "return_time", "borrow_status", "renew_count", "fine_amount",
            "created_at", "updated_at",
        ),
        {
            "borrow_id": "id_prefix",
            "reader_id": "id_prefix",
            "reader_home_campus_id": "campus",
        },
    ),
}


PHYSICAL_FRAGMENT_TABLES = {
    table.physical_name
    for table in LOGICAL_TABLES.values()
    if table.location == "fragmented"
}
