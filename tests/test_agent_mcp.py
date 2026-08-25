from types import SimpleNamespace

import httpx
import pytest

from mcp_ai_agent_lab import agent_mcp
from mcp_ai_agent_lab.agent_mcp import Phase4AgentMcpRunner
from mcp_ai_agent_lab.backend_client import DiagnosticsClient
from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.errors import McpConnectionError
from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.models import DiagnosticReport
from mcp_ai_agent_lab.tools import FunctionTools


def make_runner() -> Phase4AgentMcpRunner:
    app = create_app()
    tools = FunctionTools(
        DiagnosticsClient("http://test", transport=httpx.ASGITransport(app=app))
    )
    return Phase4AgentMcpRunner(Settings("http://test", "test-key", "test-model"), tools)


class FakeResult:
    final_output = DiagnosticReport(
        service="order-api",
        summary="DB pool timeout is degrading the service.",
        evidence=["status=degraded", "latency_ms=842", "DB connection pool timeout"],
        recommended_action="restart_service",
    )
    context_wrapper = SimpleNamespace(
        usage=SimpleNamespace(requests=2, input_tokens=41, output_tokens=19, total_tokens=60)
    )
    raw_responses = [SimpleNamespace(raw_usage={}), SimpleNamespace(raw_usage={})]

    def final_output_as(self, output_type, *, raise_if_incorrect_type=False):
        assert output_type is DiagnosticReport
        assert raise_if_incorrect_type is True
        return self.final_output


@pytest.mark.asyncio
async def test_local_function_and_mcp_use_the_same_required_tools(monkeypatch) -> None:
    runner = make_runner()

    class FakeMcpServer:
        def __init__(self, *, observations, **_):
            self.observations = observations

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def call_tool(self, name, arguments, _meta=None):
            result = await runner._tools.execute(name, arguments)
            self.observations.append(
                agent_mcp.ToolObservation(
                    selected_tool=name,
                    tool_arguments=arguments,
                    tool_result=result,
                    tool_latency_ms=1,
                )
            )
            return SimpleNamespace(structuredContent=result)

    async def fake_run(agent, _question, **_):
        if agent.mcp_servers:
            server = agent.mcp_servers[0]
            await server.call_tool("get_recent_logs", {"service": "order-api", "limit": 10})
            await server.call_tool("get_service_status", {"service": "order-api"})
            await server.call_tool("get_recent_metrics", {"service": "order-api"})
        else:
            tools = {tool.name: tool for tool in agent.tools}
            await tools["get_recent_logs"].__wrapped__(service="order-api", limit=10)
            await tools["get_service_status"].__wrapped__(service="order-api")
            await tools["get_recent_metrics"].__wrapped__(service="order-api")
        return FakeResult()

    monkeypatch.setattr(agent_mcp, "RecordingMCPServerStdio", FakeMcpServer)
    monkeypatch.setattr(agent_mcp.Runner, "run", fake_run)

    result = await runner.run("Investigate slow order-api responses.")

    expected_order = ["get_recent_logs", "get_service_status", "get_recent_metrics"]
    assert [call.selected_tool for call in result.local_function.tool_calls] == expected_order
    assert [call.selected_tool for call in result.mcp.tool_calls] == expected_order
    assert result.local_function.usage is not None
    assert result.mcp.usage is not None
    assert result.local_function.usage.total_tokens == result.mcp.usage.total_tokens == 60


@pytest.mark.asyncio
async def test_mcp_connection_error_is_exposed_as_mcp_connection_error(monkeypatch) -> None:
    runner = make_runner()

    class FailingMcpServer:
        def __init__(self, **_):
            pass

        async def __aenter__(self):
            raise RuntimeError("stdio server unavailable")

        async def __aexit__(self, *_):
            return None

    monkeypatch.setattr(agent_mcp, "RecordingMCPServerStdio", FailingMcpServer)

    with pytest.raises(McpConnectionError, match="Unable to connect"):
        await runner._run_mcp("Investigate slow order-api responses.")
