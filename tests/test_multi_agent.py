from types import SimpleNamespace

import pytest

from mcp_ai_agent_lab import multi_agent
from mcp_ai_agent_lab.config import Settings
from mcp_ai_agent_lab.fixtures import fixture_state
from mcp_ai_agent_lab.models import DiagnosticReport, ToolObservation
from mcp_ai_agent_lab.multi_agent import Phase6MultiAgentRunner


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
            usage=SimpleNamespace(requests=3, input_tokens=61, output_tokens=29, total_tokens=90)
        )
        self.raw_responses = [SimpleNamespace(raw_usage={})]

    def to_state(self):
        return self._state

    def final_output_as(self, output_type, *, raise_if_incorrect_type=False):
        assert output_type is DiagnosticReport
        assert raise_if_incorrect_type is True
        return DiagnosticReport(
            service="order-api",
            summary="Operations result completed.",
            evidence=["status=degraded"],
            recommended_action="restart_service",
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", ["approved", "rejected"])
async def test_multi_agent_handoff_preserves_tool_separation_and_approval(
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
        if isinstance(input_value, str):
            await agent.handoffs[0].on_invoke_handoff(None)
            FakeMcpServer.instances[0].observations.append(
                ToolObservation(
                    selected_tool="get_service_status",
                    tool_arguments={"service": "order-api"},
                    tool_result={"status": "degraded"},
                    tool_latency_ms=1.0,
                    agent_name="Diagnostics Agent",
                )
            )
            return FakeResult([interruption], state)
        assert input_value is state
        if state.decision == "approved":
            FakeMcpServer.instances[1].observations.append(
                ToolObservation(
                    selected_tool="restart_service",
                    tool_arguments={"service": "order-api"},
                    tool_result={"status": "healthy"},
                    tool_latency_ms=1.0,
                    agent_name="Operations Agent",
                )
            )
            fixture_state.restart()
        return FakeResult([], state)

    FakeMcpServer.instances = []
    monkeypatch.setattr(multi_agent, "RecordingMCPServerStdio", FakeMcpServer)
    monkeypatch.setattr(multi_agent.Runner, "run", fake_run)
    runner = Phase6MultiAgentRunner(Settings("http://test", "test-key", "test-model"))

    pending = await runner.start("explicit_handoff")

    assert pending.handoffs[0].from_agent == "Diagnostics Agent"
    assert pending.handoffs[0].to_agent == "Operations Agent"
    assert FakeMcpServer.instances[0].kwargs["tool_filter"] == {
        "allowed_tool_names": [
            "get_service_status",
            "get_recent_metrics",
            "get_recent_logs",
        ]
    }
    assert FakeMcpServer.instances[1].kwargs["tool_filter"] == {
        "allowed_tool_names": ["get_service_status", "restart_service"]
    }
    assert FakeMcpServer.instances[1].kwargs["require_approval"] == {
        "restart_service": "always"
    }

    completed = await runner.resume(pending.run_id, decision)

    restart_calls = [
        call for call in completed.tool_calls if call.selected_tool == "restart_service"
    ]
    assert bool(restart_calls) is (decision == "approved")
    assert completed.service_status.status == (
        "healthy" if decision == "approved" else "degraded"
    )
    assert all(server.closed for server in FakeMcpServer.instances)
    fixture_state.reset()
