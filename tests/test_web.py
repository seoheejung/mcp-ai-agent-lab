import httpx
import pytest

from mcp_ai_agent_lab.fixtures import fixture_state
from mcp_ai_agent_lab.main import create_app
from mcp_ai_agent_lab.models import (
    ApprovalRequest,
    HandoffObservation,
    MultiAgentRunResult,
    ServiceStatus,
    ToolObservation,
)


class FakePhase6Runner:
    async def start(self, experiment: str) -> MultiAgentRunResult:
        fixture_state.reset()
        return self._result(experiment, "pending_approval", None, "degraded")

    async def resume(self, _run_id: str, decision: str) -> MultiAgentRunResult:
        status = "healthy" if decision == "approved" else "degraded"
        return self._result("explicit_handoff", "completed", decision, status)

    @staticmethod
    def _result(
        experiment: str,
        state: str,
        decision: str | None,
        status: str,
    ) -> MultiAgentRunResult:
        tool_calls = [
            ToolObservation(
                selected_tool="get_service_status",
                tool_arguments={"service": "order-api"},
                tool_result={"status": "degraded"},
                tool_latency_ms=1.0,
                agent_name="Diagnostics Agent",
            )
        ]
        if decision == "approved":
            tool_calls.append(
                ToolObservation(
                    selected_tool="restart_service",
                    tool_arguments={"service": "order-api"},
                    tool_result={"status": "healthy"},
                    tool_latency_ms=1.0,
                    agent_name="Operations Agent",
                )
            )
        return MultiAgentRunResult(
            run_id="run_123",
            experiment=experiment,
            state=state,
            approval=ApprovalRequest(
                tool_name="restart_service",
                tool_arguments={"service": "order-api"},
            ),
            approval_count=1,
            approval_decision=decision,
            report=None,
            tool_calls=tool_calls,
            handoffs=[
                HandoffObservation(
                    from_agent="Diagnostics Agent",
                    to_agent="Operations Agent",
                )
            ],
            llm_requests=1,
            usage=None,
            end_to_end_ms=1.0,
            approval_wait_ms=0.0,
            required_evidence=["get_service_status"],
            trace=None,
            service_status=ServiceStatus(
                service="order-api",
                status=status,
                checked_at="2026-08-25T09:00:00+09:00",
            ),
        )


@pytest.mark.asyncio
async def test_web_application_and_multi_agent_approval_api_are_available() -> None:
    app = create_app()
    app.state.phase6_runner = FakePhase6Runner()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        page = await client.get("/")
        pending = await client.post("/api/multi-agent/explicit_handoff/start")
        approved = await client.post("/api/multi-agent/run_123/approve")
        rejected = await client.post("/api/multi-agent/run_123/reject")

    assert page.status_code == 200
    assert "RUN EXPLICIT HANDOFF" in page.text
    assert "RUN AUTONOMOUS DECISION" in page.text
    assert "APPROVE RESTART" in page.text
    assert pending.json()["state"] == "pending_approval"
    assert pending.json()["handoffs"] == [
        {"from_agent": "Diagnostics Agent", "to_agent": "Operations Agent"}
    ]
    assert approved.json()["approval_decision"] == "approved"
    assert approved.json()["tool_calls"][-1]["agent_name"] == "Operations Agent"
    assert rejected.json()["approval_decision"] == "rejected"
