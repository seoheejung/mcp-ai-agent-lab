from __future__ import annotations

from typing import Any

from .backend_client import DiagnosticsClient
from .errors import FunctionToolError

FUNCTION_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_service_status",
        "description": "Get the current diagnostics status for one service.",
        "parameters": {
            "type": "object",
            "properties": {"service": {"type": "string"}},
            "required": ["service"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_recent_metrics",
        "description": "Get recent latency, error-rate, and request-count metrics for one service.",
        "parameters": {
            "type": "object",
            "properties": {"service": {"type": "string"}},
            "required": ["service"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_recent_logs",
        "description": "Get recent error and warning logs for one service.",
        "parameters": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "required": ["service", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


class FunctionTools:
    def __init__(self, client: DiagnosticsClient) -> None:
        self._client = client

    async def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        service = arguments.get("service")
        if not isinstance(service, str) or not service:
            raise FunctionToolError("Function tool requires a service argument")

        if name == "get_service_status":
            return (await self._client.get_service_status(service)).model_dump(mode="json")
        if name == "get_recent_metrics":
            return (await self._client.get_recent_metrics(service)).model_dump(mode="json")
        if name == "get_recent_logs":
            limit = arguments.get("limit", 10)
            if not isinstance(limit, int):
                raise FunctionToolError("get_recent_logs limit must be an integer")
            return (await self._client.get_recent_logs(service, limit)).model_dump(mode="json")
        raise FunctionToolError(f"Unsupported function tool: {name}")
