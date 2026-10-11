from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any

from backend.common.models import QueryEvent


class EventBus:
    def __init__(self, max_events: int = 1000) -> None:
        self._events: deque[QueryEvent] = deque(maxlen=max_events)
        self._subscribers: set[asyncio.Queue[QueryEvent]] = set()
        self._lock = asyncio.Lock()

    async def publish(
        self,
        query_id: str,
        source: str,
        event_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> QueryEvent:
        event = QueryEvent(
            query_id=query_id,
            timestamp=datetime.now(timezone.utc),
            source=source,
            event_type=event_type,
            message=message,
            details=details or {},
        )
        async with self._lock:
            self._events.append(event)
            subscribers = tuple(self._subscribers)
        for queue in subscribers:
            if not queue.full():
                queue.put_nowait(event)
        return event

    async def subscribe(self) -> asyncio.Queue[QueryEvent]:
        queue: asyncio.Queue[QueryEvent] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[QueryEvent]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    def for_query(self, query_id: str) -> list[QueryEvent]:
        return [event for event in self._events if event.query_id == query_id]

    def recent(self) -> list[QueryEvent]:
        return list(self._events)
