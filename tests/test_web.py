import httpx
import pytest

from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.models import (
    McpToolCallResult,
    McpToolDefinition,
    McpVerificationResult,
)


class FakePhase3McpClient:
    async def verify(self) -> McpVerificationResult:
        return McpVerificationResult(
            tools=[
                McpToolDefinition(
                    name="get_service_status",
                    description="Get status.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                )
            ],
            tool_calls=[
                McpToolCallResult(
                    selected_tool="get_service_status",
                    tool_arguments={"service": "order-api"},
                    tool_result={"status": "degraded"},
                    tool_latency_ms=1.0,
                )
            ],
            end_to_end_ms=1.0,
        )


@pytest.mark.asyncio
async def test_web_application_and_mcp_verification_api_are_available() -> None:
    app = create_app()
    app.state.phase3_mcp_client = FakePhase3McpClient()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        page = await client.get("/")
        result = await client.post("/api/mcp/verification")

    assert page.status_code == 200
    assert "RUN MCP VERIFICATION" in page.text
    assert result.status_code == 200
    assert result.json()["tools"][0]["name"] == "get_service_status"
