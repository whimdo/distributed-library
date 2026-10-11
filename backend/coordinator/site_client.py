from __future__ import annotations

import asyncio

import httpx

from backend.common.event_bus import EventBus
from backend.common.models import SiteExecuteRequest, SiteExecuteResponse
from backend.common.models import CopyAdminUpdate, ReaderAdminUpdate


class SiteExecutionError(RuntimeError):
    pass


class SiteClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        site_urls: dict[int, str],
        token: str,
        event_bus: EventBus,
    ) -> None:
        self._client = client
        self._site_urls = site_urls
        self._token = token
        self._event_bus = event_bus

    async def execute(
        self,
        site_id: int,
        request: SiteExecuteRequest,
    ) -> SiteExecuteResponse:
        await self._event_bus.publish(
            request.query_id,
            "coordinator",
            "REMOTE_COMMAND_SENT",
            f"向 Site {site_id} 发送物理查询。",
            {"site_id": site_id, "sql": request.sql},
        )
        try:
            response = await self._client.post(
                f"{self._site_urls[site_id]}/internal/execute",
                headers={"X-Internal-Token": self._token},
                json=request.model_dump(),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            await self._event_bus.publish(
                request.query_id,
                "coordinator",
                "ERROR_OCCURRED",
                f"Site {site_id} 查询失败：{exc}",
                {"site_id": site_id},
            )
            raise SiteExecutionError(f"Site {site_id} 查询失败：{exc}") from exc
        result = SiteExecuteResponse.model_validate(response.json())
        await self._event_bus.publish(
            request.query_id,
            "coordinator",
            "REMOTE_RESULT_RECEIVED",
            f"收到 Site {site_id} 返回的 {result.row_count} 行结果。",
            {"site_id": site_id, "row_count": result.row_count},
        )
        return result

    async def execute_many(
        self,
        site_ids: list[int],
        request: SiteExecuteRequest,
    ) -> list[SiteExecuteResponse]:
        return list(
            await asyncio.gather(
                *(self.execute(site_id, request) for site_id in site_ids)
            )
        )

    async def update_reader(
        self, site_id: int, reader_id: int, request: ReaderAdminUpdate
    ) -> dict[str, object]:
        return await self._patch_admin_resource(
            site_id, f"readers/{reader_id}", request.model_dump()
        )

    async def update_copy(
        self, site_id: int, copy_id: int, request: CopyAdminUpdate
    ) -> dict[str, object]:
        return await self._patch_admin_resource(
            site_id, f"copies/{copy_id}", request.model_dump()
        )

    async def _patch_admin_resource(
        self, site_id: int, path: str, payload: dict[str, object]
    ) -> dict[str, object]:
        try:
            response = await self._client.patch(
                f"{self._site_urls[site_id]}/internal/admin/{path}",
                headers={"X-Internal-Token": self._token},
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise SiteExecutionError(f"Site {site_id} 更新失败：{exc}") from exc

    async def create_resource(self, site_id: int, path: str, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_resource("POST", site_id, path, payload=payload)

    async def update_resource(self, site_id: int, path: str, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_resource("PATCH", site_id, path, payload=payload)

    async def delete_resource(self, site_id: int, path: str, query_id: str) -> dict[str, object]:
        return await self._request_resource("DELETE", site_id, path, params={"query_id": query_id})

    async def _request_resource(
        self, method: str, site_id: int, path: str,
        payload: dict[str, object] | None = None,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        query_id = str((payload or {}).get("query_id") or (params or {}).get("query_id") or "")
        if query_id:
            await self._event_bus.publish(
                query_id, "coordinator", "REMOTE_WRITE_SENT",
                f"向 Site {site_id} 转发 {method} 结构化写入命令。",
                {"site_id": site_id, "method": method, "resource": path},
            )
        try:
            response = await self._client.request(
                method,
                f"{self._site_urls[site_id]}/internal/admin/{path}",
                headers={"X-Internal-Token": self._token},
                json=payload,
                params=params,
            )
            response.raise_for_status()
            result = response.json()
            if query_id:
                await self._event_bus.publish(
                    query_id, "coordinator", "REMOTE_WRITE_RESULT_RECEIVED",
                    f"收到 Site {site_id} 的写入结果。",
                    {"site_id": site_id, "resource": path},
                )
            return result
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", str(exc))
            raise SiteExecutionError(str(detail)) from exc
        except httpx.HTTPError as exc:
            raise SiteExecutionError(f"Site {site_id} 写入失败：{exc}") from exc
