import httpx
import pytest

from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.models import (
    AgentMcpComparisonResult,
    AgentMcpExecutionResult,
    DiagnosticReport,
)


class FakePhase4Runner:
    async def run(self, question: str) -> AgentMcpComparisonResult:
        execution = AgentMcpExecutionResult(
            success=True,
            report=DiagnosticReport(
                service="order-api",
                summary=question,
                evidence=["status=degraded"],
                recommended_action="none",
            ),
            tool_calls=[],
            llm_requests=1,
            usage=None,
            end_to_end_ms=1.0,
            required_evidence=[],
            trace=None,
        )
        return AgentMcpComparisonResult(
            question=question,
            local_function=execution,
            mcp=execution,
        )


@pytest.mark.asyncio
async def test_web_application_and_agent_mcp_comparison_api_are_available() -> None:
    app = create_app()
    app.state.phase4_runner = FakePhase4Runner()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        page = await client.get("/")
        result = await client.post("/api/agent-mcp/comparison")

    assert page.status_code == 200
    assert "RUN AGENT MCP COMPARISON" in page.text
    assert result.status_code == 200
    assert result.json()["local_function"]["success"] is True
