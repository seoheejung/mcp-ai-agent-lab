import httpx
import pytest

from mcp_ai_agent_lab.fixtures import fixture_state
from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.models import ApprovalRequest, ApprovalRunResult, ServiceStatus


class FakePhase5Runner:
    async def start(self) -> ApprovalRunResult:
        fixture_state.reset()
        return self._result("pending_approval", None, "degraded")

    async def resume(self, _run_id: str, decision: str) -> ApprovalRunResult:
        return self._result("completed", f"{decision}", "healthy")

    @staticmethod
    def _result(
        state: str,
        decision: str | None,
        status: str,
    ) -> ApprovalRunResult:
        return ApprovalRunResult(
            run_id="run_123",
            state=state,
            approval=ApprovalRequest(
                tool_name="restart_service",
                tool_arguments={"service": "order-api"},
            ),
            approval_count=1,
            approval_decision=decision,
            report=None,
            tool_calls=[],
            llm_requests=1,
            usage=None,
            end_to_end_ms=1.0,
            approval_wait_ms=0.0,
            required_evidence=[],
            trace=None,
            service_status=ServiceStatus(
                service="order-api",
                status=status,
                checked_at="2026-08-25T09:00:00+09:00",
            ),
        )


@pytest.mark.asyncio
async def test_web_application_and_human_approval_api_are_available() -> None:
    app = create_app()
    app.state.phase5_runner = FakePhase5Runner()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        page = await client.get("/")
        pending = await client.post("/api/human-approval/start")
        approved = await client.post("/api/human-approval/run_123/approve")
        rejected = await client.post("/api/human-approval/run_123/reject")

    assert page.status_code == 200
    assert "APPROVE RESTART" in page.text
    assert "REJECT RESTART" in page.text
    assert pending.json()["state"] == "pending_approval"
    assert pending.json()["approval"]["tool_name"] == "restart_service"
    assert approved.json()["approval_decision"] == "approved"
    assert rejected.json()["approval_decision"] == "rejected"
