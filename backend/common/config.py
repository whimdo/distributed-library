from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _database_url(database: str, port_variable: str, default_port: int) -> str:
    user = quote_plus(os.getenv("LIBRARY_DB_USER", "library_admin"))
    password = quote_plus(os.getenv("LIBRARY_DB_PASSWORD", "library_password"))
    host = os.getenv("LIBRARY_DB_HOST", "127.0.0.1")
    port = int(os.getenv(port_variable, str(default_port)))
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


@dataclass(frozen=True)
class Settings:
    coordinator_database_url: str
    site_database_urls: dict[int, str]
    site_api_urls: dict[int, str]
    internal_api_token: str
    query_timeout_seconds: float
    max_result_rows: int
    auth_secret: str
    access_token_minutes: int


def get_settings() -> Settings:
    return Settings(
        coordinator_database_url=os.getenv(
            "COORDINATOR_DATABASE_URL",
            _database_url("coordinator_db", "COORDINATOR_DB_PORT", 5436),
        ),
        site_database_urls={
            1: os.getenv(
                "SITE1_DATABASE_URL",
                _database_url("site1_db", "SITE1_DB_PORT", 5433),
            ),
            2: os.getenv(
                "SITE2_DATABASE_URL",
                _database_url("site2_db", "SITE2_DB_PORT", 5434),
            ),
            3: os.getenv(
                "SITE3_DATABASE_URL",
                _database_url("site3_db", "SITE3_DB_PORT", 5435),
            ),
        },
        site_api_urls={
            1: os.getenv("SITE1_API_URL", "http://127.0.0.1:8001"),
            2: os.getenv("SITE2_API_URL", "http://127.0.0.1:8002"),
            3: os.getenv("SITE3_API_URL", "http://127.0.0.1:8003"),
        },
        internal_api_token=os.getenv(
            "INTERNAL_API_TOKEN",
            "distributed-library-development-token",
        ),
        query_timeout_seconds=float(os.getenv("QUERY_TIMEOUT_SECONDS", "10")),
        max_result_rows=int(os.getenv("MAX_RESULT_ROWS", "500")),
        auth_secret=os.getenv(
            "AUTH_SECRET",
            "local-coursework-secret-change-before-deployment",
        ),
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "480")),
    )
