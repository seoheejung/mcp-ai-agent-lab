from types import SimpleNamespace

import pytest

from mcp_ai_agent_lab import human_approval
from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.fixtures import fixture_state
from mcp_ai_agent_lab.human_approval import Phase5HumanApprovalRunner
from mcp_ai_agent_lab.models import DiagnosticReport, ToolObservation


class FakeRunState:
    def __init__(self) -> None:
        self.decision: str | None = None

    def approve(self, _interruption) -> None:
        self.decision = "approved"

    def reject(self, _interruption, **_) -> None:
        self.decision = "rejected"


class FakeMcpServer:
    instances: list["FakeMcpServer"] = []

    def __init__(self, *, observations, **kwargs) -> None:
        self.observations = observations
        self.kwargs = kwargs
        self.closed = False
        self.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        self.closed = True


class FakeResult:
    def __init__(self, interruptions, state: FakeRunState) -> None:
        self.interruptions = interruptions
        self._state = state
        self.context_wrapper = SimpleNamespace(
            usage=SimpleNamespace(requests=2, input_tokens=41, output_tokens=19, total_tokens=60)
        )
        self.raw_responses = [SimpleNamespace(raw_usage={})]

    def to_state(self):
        return self._state

    def final_output_as(self, output_type, *, raise_if_incorrect_type=False):
        assert output_type is DiagnosticReport
        assert raise_if_incorrect_type is True
        return DiagnosticReport(
            service="order-api",
            summary="Restart decision completed.",
            evidence=["status=degraded", "latency_ms=842", "DB connection pool timeout"],
            recommended_action="restart_service",
        )


def _read_observations() -> list[ToolObservation]:
    return [
        ToolObservation(
            selected_tool="get_service_status",
            tool_arguments={"service": "order-api"},
            tool_result={"status": "degraded"},
            tool_latency_ms=1.0,
        ),
        ToolObservation(
            selected_tool="get_recent_metrics",
            tool_arguments={"service": "order-api"},
            tool_result={"latency_ms": 842},
            tool_latency_ms=1.0,
        ),
        ToolObservation(
            selected_tool="get_recent_logs",
            tool_arguments={"service": "order-api", "limit": 10},
            tool_result={"entries": []},
            tool_latency_ms=1.0,
        ),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", ["approved", "rejected"])
async def test_approval_interrupts_then_resumes_the_same_run_state(
    monkeypatch,
    decision: str,
) -> None:
    fixture_state.reset()
    state = FakeRunState()
    interruption = SimpleNamespace(
        name="restart_service",
        tool_name="restart_service",
        arguments='{"service":"order-api"}',
    )

    async def fake_run(agent, input_value, **_):
        server = agent.mcp_servers[0]
        if isinstance(input_value, str):
            server.observations.extend(_read_observations())
            return FakeResult([interruption], state)
        assert input_value is state
        if state.decision == "approved":
            server.observations.append(
                ToolObservation(
                    selected_tool="restart_service",
                    tool_arguments={"service": "order-api"},
                    tool_result={"status": "healthy"},
                    tool_latency_ms=1.0,
                )
            )
            fixture_state.restart()
        return FakeResult([], state)

    monkeypatch.setattr(human_approval, "RecordingMCPServerStdio", FakeMcpServer)
    monkeypatch.setattr(human_approval.Runner, "run", fake_run)
    runner = Phase5HumanApprovalRunner(Settings("http://test", "test-key", "test-model"))

    pending = await runner.start()

    assert pending.state == "pending_approval"
    assert pending.service_status.status == "degraded"
    assert [call.selected_tool for call in pending.tool_calls] == [
        "get_service_status",
        "get_recent_metrics",
        "get_recent_logs",
    ]
    assert FakeMcpServer.instances[-1].kwargs["require_approval"] == {
        "restart_service": "always"
    }

    completed = await runner.resume(pending.run_id, decision)

    assert completed.state == "completed"
    assert completed.approval_decision == decision
    restart_calls = [
        call for call in completed.tool_calls if call.selected_tool == "restart_service"
    ]
    assert bool(restart_calls) is (decision == "approved")
    assert completed.service_status.status == (
        "healthy" if decision == "approved" else "degraded"
    )
    assert FakeMcpServer.instances[-1].closed is True
    fixture_state.reset()
