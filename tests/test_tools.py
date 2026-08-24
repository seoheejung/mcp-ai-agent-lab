import httpx
import pytest

from mcp_ai_agent_lab.backend_client import DiagnosticsClient
from mcp_ai_agent_lab.errors import BackendConnectionError, ServiceNotFoundError
from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.tools import FUNCTION_TOOLS, FunctionTools


@pytest.mark.asyncio
async def test_each_tool_uses_backend_api_fixture() -> None:
    tools = FunctionTools(
        DiagnosticsClient(
            "http://test",
            transport=httpx.ASGITransport(app=create_app()),
        )
    )

    status = await tools.execute("get_service_status", {"service": "order-api"})
    metrics = await tools.execute("get_recent_metrics", {"service": "order-api"})
    logs = await tools.execute("get_recent_logs", {"service": "order-api", "limit": 1})

    assert status["status"] == "degraded"
    assert metrics["latency_ms"] == 842
    assert logs["entries"][0]["message"] == "DB connection pool timeout"


@pytest.mark.asyncio
async def test_unknown_service_is_not_hidden_by_tool() -> None:
    tools = FunctionTools(
        DiagnosticsClient(
            "http://test",
            transport=httpx.ASGITransport(app=create_app()),
        )
    )

    with pytest.raises(ServiceNotFoundError):
        await tools.execute("get_service_status", {"service": "unknown-api"})


@pytest.mark.asyncio
async def test_connection_failure_is_reported() -> None:
    client = DiagnosticsClient("http://127.0.0.1:1")

    with pytest.raises(BackendConnectionError):
        await client.get_service_status("order-api")


def test_function_schemas_only_expose_read_tools() -> None:
    assert [tool["name"] for tool in FUNCTION_TOOLS] == [
        "get_service_status",
        "get_recent_metrics",
        "get_recent_logs",
    ]
    for tool in FUNCTION_TOOLS:
        parameters = tool["parameters"]
        assert tool["strict"] is True
        assert parameters["additionalProperties"] is False
        assert set(parameters["required"]) == set(parameters["properties"])
