from __future__ import annotations

import sys
from time import perf_counter
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from .config import Settings
from .errors import McpConnectionError, McpToolError
from .models import McpToolCallResult, McpToolDefinition, McpVerificationResult

NORMAL_CALLS = (
    ("get_service_status", {"service": "order-api"}),
    ("get_recent_metrics", {"service": "order-api"}),
    ("get_recent_logs", {"service": "order-api", "limit": 10}),
)


class Phase3McpClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def verify(self) -> McpVerificationResult:
        started_at = perf_counter()
        try:
            async with Client(self._transport()) as client:
                tools = [self._tool_definition(tool) for tool in await client.list_tools()]
                calls = [
                    await self._call_tool(client, name, arguments)
                    for name, arguments in NORMAL_CALLS
                ]
        except ToolError as error:
            raise McpToolError("MCP tool execution failed") from error
        except McpToolError:
            raise
        except Exception as error:
            raise McpConnectionError("Unable to connect to MCP server") from error

        return McpVerificationResult(
            tools=tools,
            tool_calls=calls,
            end_to_end_ms=(perf_counter() - started_at) * 1000,
        )

    async def call_tool(
        self, name: str, arguments: dict[str, object]
    ) -> McpToolCallResult:
        try:
            async with Client(self._transport()) as client:
                return await self._call_tool(client, name, arguments)
        except ToolError as error:
            raise McpToolError("MCP tool execution failed") from error
        except McpToolError:
            raise
        except Exception as error:
            raise McpConnectionError("Unable to connect to MCP server") from error

    def _transport(self) -> StdioTransport:
        return StdioTransport(
            command=sys.executable,
            args=["-m", "mcp_ai_agent_lab.mcp_server"],
            env={"BACKEND_BASE_URL": self._settings.backend_base_url},
            keep_alive=False,
        )

    async def _call_tool(
        self,
        client: Client,
        name: str,
        arguments: dict[str, object],
    ) -> McpToolCallResult:
        started_at = perf_counter()
        result = await client.call_tool(name, arguments)
        return McpToolCallResult(
            selected_tool=name,
            tool_arguments=arguments,
            tool_result=self._tool_result(result.data),
            tool_latency_ms=(perf_counter() - started_at) * 1000,
        )

    @staticmethod
    def _tool_definition(tool: Any) -> McpToolDefinition:
        payload = tool.model_dump(by_alias=True)
        return McpToolDefinition(
            name=tool.name,
            description=tool.description,
            input_schema=payload.get("inputSchema", {}),
            output_schema=payload.get("outputSchema", {}),
        )

    @staticmethod
    def _tool_result(value: Any) -> dict[str, object]:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        encoded = jsonable_encoder(value)
        if isinstance(encoded, dict):
            return encoded
        raise McpToolError("MCP tool returned an unexpected result type")
