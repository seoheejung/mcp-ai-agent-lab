import asyncio
import socket
import sys

import httpx
import pytest

from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.errors import McpToolError
from mcp_ai_agent_lab.mcp_client import Phase3McpClient


def _available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


async def _wait_for_backend(base_url: str) -> None:
    for _ in range(30):
        try:
            async with httpx.AsyncClient(base_url=base_url) as client:
                response = await client.get("/services/order-api/status")
            if response.status_code == 200:
                return
        except httpx.RequestError:
            pass
        await asyncio.sleep(0.1)
    raise RuntimeError("FastAPI Backend Diagnostics server did not start")


@pytest.mark.asyncio
async def test_stdio_mcp_discovery_calls_and_error_propagation() -> None:
    port = _available_port()
    base_url = f"http://127.0.0.1:{port}"
    server = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "uvicorn",
        "mcp_ai_agent_lab.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        await _wait_for_backend(base_url)
        client = Phase3McpClient(Settings(base_url, None, None))

        result = await client.verify()

        assert [tool.name for tool in result.tools] == [
            "get_service_status",
            "get_recent_metrics",
            "get_recent_logs",
        ]
        assert result.tools[0].input_schema["required"] == ["service"]
        assert result.tools[0].output_schema["type"] == "object"
        assert result.tools[2].input_schema["properties"]["limit"] == {
            "default": 10,
            "maximum": 100,
            "minimum": 1,
            "type": "integer",
        }
        assert result.tool_calls[0].tool_result["status"] == "degraded"
        assert result.tool_calls[1].tool_result["latency_ms"] == 842
        assert result.tool_calls[2].tool_result["entries"][0]["message"] == (
            "DB connection pool timeout"
        )

        with pytest.raises(McpToolError):
            await client.call_tool(
                "get_recent_logs",
                {"service": "order-api", "limit": 0},
            )
        with pytest.raises(McpToolError):
            await client.call_tool("get_service_status", {"service": "unknown-api"})
        with pytest.raises(McpToolError):
            await Phase3McpClient(
                Settings("http://127.0.0.1:1", None, None)
            ).call_tool("get_service_status", {"service": "order-api"})
    finally:
        server.terminate()
        await server.wait()
