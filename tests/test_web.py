import httpx
import pytest

from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.models import (
    DiagnosticComparisonResult,
    DiagnosticExecutionResult,
    DiagnosticReport,
    ToolObservation,
)


class FakePhase2Runner:
    async def run(self, question: str) -> DiagnosticComparisonResult:
        execution = DiagnosticExecutionResult(
            report=DiagnosticReport(
                service="order-api",
                summary=question,
                evidence=["status=degraded"],
                recommended_action="none",
            ),
            tool_calls=[
                ToolObservation(
                    selected_tool="get_service_status",
                    tool_arguments={"service": "order-api"},
                    tool_result={"status": "degraded"},
                    tool_latency_ms=1.0,
                )
            ],
            llm_requests=1,
            usage=None,
            end_to_end_ms=1.0,
            required_evidence=["get_service_status"],
            trace=None,
        )
        return DiagnosticComparisonResult(
            question=question,
            workflow=execution,
            agent=execution,
        )


@pytest.mark.asyncio
async def test_web_application_and_result_api_are_available() -> None:
    app = create_app()
    app.state.phase2_runner = FakePhase2Runner()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        page = await client.get("/")
        result = await client.post("/api/diagnostics", json={"question": "status?"})

    assert page.status_code == 200
    assert "RUN COMPARISON" in page.text
    assert result.status_code == 200
    assert result.json()["workflow"]["tool_calls"][0]["selected_tool"] == "get_service_status"


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
