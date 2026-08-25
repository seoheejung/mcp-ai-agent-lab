from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from .backend_client import DiagnosticsClient
from .config import Settings
from .models import RestartResult, ServiceLogs, ServiceMetrics, ServiceStatus

mcp = FastMCP("Backend Diagnostics MCP Server")


def _client() -> DiagnosticsClient:
    return DiagnosticsClient(Settings.from_environment().backend_base_url)


@mcp.tool()
async def get_service_status(service: str) -> ServiceStatus:
    """Get the current diagnostics status for one service."""
    return await _client().get_service_status(service)


@mcp.tool()
async def get_recent_metrics(service: str) -> ServiceMetrics:
    """Get recent latency, error-rate, and request-count metrics for one service."""
    return await _client().get_recent_metrics(service)


@mcp.tool()
async def get_recent_logs(
    service: str,
    limit: Annotated[int, Field(ge=1, le=100)] = 10,
) -> ServiceLogs:
    """Get recent error and warning logs for one service."""
    return await _client().get_recent_logs(service, limit)


@mcp.tool()
async def restart_service(service: str) -> RestartResult:
    """Restart one degraded service after human approval."""
    return await _client().restart_service(service)


if __name__ == "__main__":
    mcp.run(transport="stdio")
