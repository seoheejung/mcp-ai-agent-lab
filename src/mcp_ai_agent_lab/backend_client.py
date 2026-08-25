from __future__ import annotations

from typing import Any

import httpx

from .errors import BackendConnectionError, BackendResponseError, ServiceNotFoundError
from .models import RestartResult, ServiceLogs, ServiceMetrics, ServiceStatus


class DiagnosticsClient:
    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def get_service_status(self, service: str) -> ServiceStatus:
        payload = await self._get(f"/services/{service}/status")
        return ServiceStatus.model_validate(payload)

    async def get_recent_metrics(self, service: str) -> ServiceMetrics:
        payload = await self._get(f"/services/{service}/metrics")
        return ServiceMetrics.model_validate(payload)

    async def get_recent_logs(self, service: str, limit: int = 10) -> ServiceLogs:
        payload = await self._get(f"/services/{service}/logs", params={"limit": limit})
        return ServiceLogs.model_validate(payload)

    async def restart_service(self, service: str) -> RestartResult:
        payload = await self._post(f"/services/{service}/restart")
        return RestartResult.model_validate(payload)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str) -> dict[str, Any]:
        return await self._request("POST", path)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                transport=self._transport,
                timeout=httpx.Timeout(10.0),
            ) as client:
                response = await client.request(method, path, params=params)
        except httpx.RequestError as error:
            raise BackendConnectionError("Unable to connect to Backend Diagnostics API") from error

        if response.status_code == 404:
            raise ServiceNotFoundError(response.json().get("detail", "Service not found"))
        if response.is_error:
            raise BackendResponseError(f"Backend Diagnostics API returned {response.status_code}")
        return response.json()
