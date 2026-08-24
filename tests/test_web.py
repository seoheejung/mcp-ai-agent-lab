import httpx
import pytest

from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.models import (
    DiagnosticReport,
    DiagnosticRunResult,
    ToolObservation,
)


class FakeRunner:
    async def run(self, question: str) -> DiagnosticRunResult:
        return DiagnosticRunResult(
            report=DiagnosticReport(
                service="order-api",
                summary=question,
                evidence=["status=degraded"],
                recommended_action="none",
            ),
            observation=ToolObservation(
                selected_tool="get_service_status",
                tool_arguments={"service": "order-api"},
                tool_result={"status": "degraded"},
                tool_latency_ms=1.0,
            ),
            usage=None,
        )


@pytest.mark.asyncio
async def test_web_application_and_result_api_are_available() -> None:
    app = create_app()
    app.state.diagnostic_runner = FakeRunner()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        page = await client.get("/")
        result = await client.post("/api/diagnostics", json={"question": "status?"})

    assert page.status_code == 200
    assert "RUN TOOL CALL" in page.text
    assert result.status_code == 200
    assert result.json()["observation"]["selected_tool"] == "get_service_status"


@pytest.mark.asyncio
async def test_missing_openai_configuration_is_displayable_error() -> None:
    app = create_app(Settings("http://test", None, None))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        result = await client.post(
            "/api/diagnostics", json={"question": "order-api 상태를 확인해줘."}
        )

    assert result.status_code == 503
    assert result.json()["error_type"] == "configuration_error"
