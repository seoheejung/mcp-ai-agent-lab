from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from .fixtures import SERVICE_LOGS, SERVICE_METRICS, SERVICE_NAME, fixture_state
from .models import RestartResult, ServiceLogs, ServiceMetrics, ServiceStatus


def _require_service(service: str) -> None:
    if service != SERVICE_NAME:
        raise HTTPException(status_code=404, detail=f"Service not found: {service}")


def register_diagnostics_routes(app: FastAPI) -> None:
    @app.get("/services/{service}/status", response_model=ServiceStatus)
    async def get_status(service: str) -> ServiceStatus:
        _require_service(service)
        return fixture_state.status()

    @app.get("/services/{service}/metrics", response_model=ServiceMetrics)
    async def get_metrics(service: str) -> ServiceMetrics:
        _require_service(service)
        return SERVICE_METRICS

    @app.get("/services/{service}/logs", response_model=ServiceLogs)
    async def get_logs(
        service: str,
        limit: int = Query(default=10, ge=1, le=100),
    ) -> ServiceLogs:
        _require_service(service)
        return SERVICE_LOGS.model_copy(update={"entries": SERVICE_LOGS.entries[:limit]})

    @app.post("/services/{service}/restart", response_model=RestartResult)
    async def restart_service(service: str) -> RestartResult:
        _require_service(service)
        return fixture_state.restart()
