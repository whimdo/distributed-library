from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=20_000)


class QueryEvent(BaseModel):
    query_id: str
    timestamp: datetime
    source: str
    event_type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class PhysicalQueryInfo(BaseModel):
    target: str
    sql: str


class QueryResponse(BaseModel):
    query_id: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    selected_sites: list[int]
    physical_queries: list[PhysicalQueryInfo]
    events: list[QueryEvent]


class SiteExecuteRequest(BaseModel):
    query_id: str
    sql: str = Field(min_length=1, max_length=20_000)
    logical_tables: list[str] = Field(default_factory=list)


class SiteExecuteResponse(BaseModel):
    query_id: str
    site_id: int
    database: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class AuthUser(BaseModel):
    account_id: int
    username: str
    display_name: str
    role: str
    reader_id: int | None = None
    home_site_id: int | None = None
    managed_site_id: int | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class ReaderAdminUpdate(BaseModel):
    query_id: str = ""
    status: str | None = None
    network_permission: bool | None = None
    max_borrow_count: int | None = Field(default=None, ge=0, le=100)
    reader_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    reader_type: str | None = None


class ReaderAdminCreate(BaseModel):
    query_id: str = ""
    home_university_id: int
    home_campus_id: int
    student_no: str = Field(min_length=1, max_length=100)
    network_card_no: str = Field(min_length=1, max_length=100)
    reader_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    reader_type: str
    network_permission: bool = True
    max_borrow_count: int = Field(default=10, ge=0, le=100)
    status: str = "ACTIVE"


class CopyAdminUpdate(BaseModel):
    query_id: str = ""
    copy_status: str | None = None
    allow_cross_borrow: bool | None = None
    shelf_location: str | None = Field(default=None, max_length=100)
    current_library_id: int | None = None
    acquisition_date: date | None = None
    price: float | None = Field(default=None, ge=0)


class CopyAdminCreate(BaseModel):
    query_id: str = ""
    book_id: int
    owner_university_id: int
    owner_campus_id: int
    owner_library_id: int
    current_library_id: int
    barcode: str = Field(min_length=1, max_length=100)
    shelf_location: str | None = Field(default=None, max_length=100)
    copy_status: str = "AVAILABLE"
    allow_cross_borrow: bool = True
    acquisition_date: date | None = None
    price: float | None = Field(default=None, ge=0)


class BorrowAdminCreate(BaseModel):
    query_id: str = ""
    reader_id: int
    reader_home_campus_id: int
    book_id: int
    copy_id: int
    copy_owner_site_id: int = Field(ge=1, le=3)
    checkout_library_id: int
    return_library_id: int | None = None
    borrow_type: str
    borrow_time: datetime
    due_time: datetime
    return_time: datetime | None = None
    borrow_status: str = "BORROWING"
    renew_count: int = Field(default=0, ge=0)
    fine_amount: float = Field(default=0, ge=0)


class BorrowAdminUpdate(BaseModel):
    query_id: str = ""
    return_library_id: int | None = None
    due_time: datetime | None = None
    return_time: datetime | None = None
    borrow_status: str | None = None
    renew_count: int | None = Field(default=None, ge=0)
    fine_amount: float | None = Field(default=None, ge=0)


class LibraryAdminCreate(BaseModel):
    query_id: str = ""
    university_id: int
    campus_id: int
    library_name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=500)
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    service_radius_m: int = Field(gt=0, le=100000)
    open_time: time
    close_time: time
    phone: str = Field(min_length=1, max_length=50)
    total_seats: int = Field(ge=0)
    status: str = "OPEN"


class LibraryAdminUpdate(BaseModel):
    query_id: str = ""
    library_name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    service_radius_m: int | None = Field(default=None, gt=0, le=100000)
    open_time: time | None = None
    close_time: time | None = None
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    total_seats: int | None = Field(default=None, ge=0)
    status: str | None = None
