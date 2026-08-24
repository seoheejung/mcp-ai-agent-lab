from types import SimpleNamespace

import httpx
import pytest

from mcp_ai_agent_lab.backend_client import DiagnosticsClient
from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.models import DiagnosticReport
from mcp_ai_agent_lab.runner import ToolCallingRunner
from mcp_ai_agent_lab.tools import FunctionTools


class FakeResponses:
    def __init__(self) -> None:
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            async def events():
                yield SimpleNamespace(type="response.created")
                yield SimpleNamespace(type="response.completed")

            return events()
        if len(self.calls) == 1:
            return SimpleNamespace(
                output=[
                    SimpleNamespace(
                        type="function_call",
                        name="get_service_status",
                        arguments='{"service":"order-api"}',
                        call_id="call_123",
                    )
                ],
                usage=SimpleNamespace(input_tokens=11, output_tokens=4),
            )
        return SimpleNamespace(
            output_text=(
                '{"service":"order-api","summary":"order-api is degraded.",'
                '"evidence":["status=degraded"],"recommended_action":"none"}'
            ),
            usage=SimpleNamespace(input_tokens=22, output_tokens=9),
        )


class FakeOpenAI:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def make_runner() -> tuple[ToolCallingRunner, FakeOpenAI]:
    client = FakeOpenAI()
    tools = FunctionTools(
        DiagnosticsClient("http://test", transport=httpx.ASGITransport(app=create_app()))
    )
    runner = ToolCallingRunner(
        Settings("http://test", "test-key", "test-model"), tools, client=client
    )
    return runner, client


@pytest.mark.asyncio
async def test_runner_executes_one_selected_function_and_validates_report() -> None:
    runner, client = make_runner()

    result = await runner.run("order-api 상태를 확인해줘.")

    assert result.observation.selected_tool == "get_service_status"
    assert result.report.service == "order-api"
    assert result.usage is not None
    assert result.usage.total_tokens == 46
    assert len(client.responses.calls) == 2
    assert "tools" not in client.responses.calls[1]


@pytest.mark.asyncio
async def test_streaming_check_records_response_events() -> None:
    runner, _ = make_runner()

    result = await runner.verify_streaming()

    assert result.event_types == ["response.created", "response.completed"]


def test_structured_report_schema_forbids_extra_properties() -> None:
    schema = DiagnosticReport.model_json_schema()

    assert schema["additionalProperties"] is False
