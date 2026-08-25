from types import SimpleNamespace

import httpx
import pytest
from agents import RunConfig
from agents.tool_context import ToolContext

from mcp_ai_agent_lab import agent_loop
from mcp_ai_agent_lab.agent_loop import Phase2DiagnosticsRunner, REQUIRED_TOOL_NAMES
from mcp_ai_agent_lab.backend_client import DiagnosticsClient
from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.errors import LlmResponseError
from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.models import DiagnosticReport
from mcp_ai_agent_lab.tools import FunctionTools


class FakeWorkflowResponses:
    def __init__(self) -> None:
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_text=(
                '{"service":"order-api","summary":"DB pool timeout is degrading the service.",'
                '"evidence":["status=degraded","latency_ms=842","DB connection pool timeout"],'
                '"recommended_action":"restart_service"}'
            ),
            usage=SimpleNamespace(input_tokens=31, output_tokens=17),
        )


class FakeAsyncOpenAI:
    responses = FakeWorkflowResponses()

    def __init__(self, **_):
        pass


def make_runner() -> Phase2DiagnosticsRunner:
    app = create_app()
    tools = FunctionTools(
        DiagnosticsClient("http://test", transport=httpx.ASGITransport(app=app))
    )
    return Phase2DiagnosticsRunner(Settings("http://test", "test-key", "test-model"), tools)


@pytest.mark.asyncio
async def test_workflow_calls_each_required_tool_before_one_llm_request(monkeypatch) -> None:
    monkeypatch.setattr(agent_loop, "AsyncOpenAI", FakeAsyncOpenAI)
    runner = make_runner()

    result = await runner._run_workflow("Investigate slow order-api responses.")

    assert [call.selected_tool for call in result.tool_calls] == list(REQUIRED_TOOL_NAMES)
    assert result.llm_requests == 1
    assert result.usage is not None
    assert result.usage.total_tokens == 48
    assert result.required_evidence == list(REQUIRED_TOOL_NAMES)
    assert result.trace is not None
    assert result.trace.span_types == ["function", "function", "function", "generation"]


@pytest.mark.asyncio
async def test_agent_records_agent_selected_tool_order_and_usage(monkeypatch) -> None:
    runner = make_runner()

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

    async def fake_run(agent, question, **_):
        assert question == "Investigate slow order-api responses."
        tools_by_name = {tool.name: tool for tool in agent.tools}
        await tools_by_name["get_recent_logs"].__wrapped__(
            service="order-api", limit=10
        )
        await tools_by_name["get_service_status"].__wrapped__(service="order-api")
        await tools_by_name["get_recent_metrics"].__wrapped__(service="order-api")
        return FakeResult()

    monkeypatch.setattr(agent_loop.Runner, "run", fake_run)

    result = await runner._run_agent("Investigate slow order-api responses.")

    assert [call.selected_tool for call in result.tool_calls] == [
        "get_recent_logs",
        "get_service_status",
        "get_recent_metrics",
    ]
    assert result.llm_requests == 2
    assert result.usage is not None
    assert result.usage.total_tokens == 60
    assert result.required_evidence == list(REQUIRED_TOOL_NAMES)


@pytest.mark.asyncio
async def test_agent_does_not_report_success_after_a_tool_error(monkeypatch) -> None:
    runner = make_runner()

    class FakeResult:
        final_output = DiagnosticReport(
            service="unknown-api",
            summary="The service could not be found.",
            evidence=[],
            recommended_action="none",
        )
        context_wrapper = SimpleNamespace(
            usage=SimpleNamespace(requests=1, input_tokens=1, output_tokens=1, total_tokens=2)
        )
        raw_responses = [SimpleNamespace(raw_usage={})]

        def final_output_as(self, *_args, **_kwargs):
            return self.final_output

    async def fake_run(agent, _question, **_):
        status_tool = next(tool for tool in agent.tools if tool.name == "get_service_status")
        output = await status_tool.on_invoke_tool(
            ToolContext(
                None,
                tool_name="get_service_status",
                tool_call_id="call_123",
                tool_arguments='{"service":"unknown-api"}',
                run_config=RunConfig(trace_include_sensitive_data=False),
            ),
            '{"service":"unknown-api"}',
        )
        assert "Service not found" in output
        return FakeResult()

    monkeypatch.setattr(agent_loop.Runner, "run", fake_run)

    with pytest.raises(LlmResponseError, match="did not collect all required evidence"):
        await runner._run_agent("Investigate unknown-api.")
