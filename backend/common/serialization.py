from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID


def json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, Mapping):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return str(value)


def record_to_dict(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: json_value(value) for key, value in record.items()}
