from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from agents import Agent, ModelSettings, RunConfig, RunState, Runner, handoff, trace
from agents.items import ToolApprovalItem
from agents.models.openai_responses import OpenAIResponsesModel
from openai import AsyncOpenAI

from .agent_loop import DIAGNOSTICS_AGENT_NAME, TRACE_RECORDER, _agent_usage, _required_evidence
from .agent_mcp import RecordingMCPServerStdio
from .config import Settings
from .errors import AgentRunError, ApprovalRejectionError, LlmResponseError, McpConnectionError
from .fixtures import fixture_state
from .models import (
    ApprovalRequest,
    DiagnosticReport,
    HandoffObservation,
    MultiAgentRunResult,
    ToolObservation,
)

OPERATIONS_AGENT_NAME = "Operations Agent"
EXPLICIT_HANDOFF_QUESTION = "order-api 상태를 확인한 뒤 재시작 작업을 Operations Agent에게 위임해줘."
AUTONOMOUS_DECISION_QUESTION = "order-api의 응답 지연 원인을 조사하고 필요한 조치를 수행해줘."
DIAGNOSTICS_INSTRUCTIONS = (
    "You are the Diagnostics Agent. Use only the read-only diagnostics tools to analyze "
    "service status, metrics, and logs. You must never restart a service. When the user "
    "explicitly asks to delegate a restart, or when your diagnosis shows restart work is "
    "needed, hand off to the Operations Agent."
)
OPERATIONS_INSTRUCTIONS = (
    "You are the Operations Agent. You may check service status and request restart_service "
    "when a restart is needed. restart_service requires human approval. After the tool outcome, "
    "produce the structured diagnostic report."
)


@dataclass
class PendingMultiAgentRun:
    diagnostics_agent: Agent
    diagnostics_server: RecordingMCPServerStdio
    operations_server: RecordingMCPServerStdio
    state: RunState
    interruption: ToolApprovalItem
    experiment: Literal["explicit_handoff", "autonomous_decision"]
    observations: list[ToolObservation]
    handoffs: list[HandoffObservation]
    started_at: float
    paused_at: float


class Phase6MultiAgentRunner:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pending_runs: dict[str, PendingMultiAgentRun] = {}

    async def start(
        self,
        experiment: Literal["explicit_handoff", "autonomous_decision"],
    ) -> MultiAgentRunResult:
        fixture_state.reset()
        observations: list[ToolObservation] = []
        handoffs: list[HandoffObservation] = []
        diagnostics_server = self._server(
            observations,
            DIAGNOSTICS_AGENT_NAME,
            ["get_service_status", "get_recent_metrics", "get_recent_logs"],
        )
        operations_server = self._server(
            observations,
            OPERATIONS_AGENT_NAME,
            ["get_service_status", "restart_service"],
            require_approval={"restart_service": "always"},
        )
        started_at = perf_counter()
        try:
            await diagnostics_server.__aenter__()
            await operations_server.__aenter__()
            diagnostics_agent = self._agents(operations_server, diagnostics_server, handoffs)
            with trace(f"phase6_{experiment}") as agent_trace:
                result = await Runner.run(
                    diagnostics_agent,
                    self._question(experiment),
                    run_config=self._run_config(experiment),
                )
            if experiment == "explicit_handoff" and not handoffs:
                raise LlmResponseError("Diagnostics Agent did not hand off to Operations Agent")
            if not result.interruptions:
                report = result.final_output_as(DiagnosticReport, raise_if_incorrect_type=True)
                await diagnostics_server.__aexit__(None, None, None)
                await operations_server.__aexit__(None, None, None)
                return self._result(
                    run_id=uuid4().hex,
                    experiment=experiment,
                    state="completed",
                    approval=None,
                    decision=None,
                    report=report,
                    observations=observations,
                    handoffs=handoffs,
                    result=result,
                    started_at=started_at,
                    approval_wait_ms=0,
                    trace_id=agent_trace.trace_id,
                )

            interruption = result.interruptions[0]
            approval = _approval_request(interruption)
            if approval.tool_name != "restart_service":
                raise LlmResponseError("Unexpected tool approval request")
            run_id = uuid4().hex
            self._pending_runs[run_id] = PendingMultiAgentRun(
                diagnostics_agent=diagnostics_agent,
                diagnostics_server=diagnostics_server,
                operations_server=operations_server,
                state=result.to_state(),
                interruption=interruption,
                experiment=experiment,
                observations=observations,
                handoffs=handoffs,
                started_at=started_at,
                paused_at=perf_counter(),
            )
            return self._result(
                run_id=run_id,
                experiment=experiment,
                state="pending_approval",
                approval=approval,
                decision=None,
                report=None,
                observations=observations,
                handoffs=handoffs,
                result=result,
                started_at=started_at,
                approval_wait_ms=0,
                trace_id=agent_trace.trace_id,
            )
        except (AgentRunError, LlmResponseError):
            await diagnostics_server.__aexit__(None, None, None)
            await operations_server.__aexit__(None, None, None)
            raise
        except Exception as error:
            await diagnostics_server.__aexit__(None, None, None)
            await operations_server.__aexit__(None, None, None)
            raise McpConnectionError("Unable to start multi-agent MCP Servers") from error

    async def resume(
        self,
        run_id: str,
        decision: Literal["approved", "rejected"],
    ) -> MultiAgentRunResult:
        pending = self._pending_runs.pop(run_id, None)
        if pending is None:
            raise ApprovalRejectionError("Approval run was not found or already resolved")
        approval_wait_ms = (perf_counter() - pending.paused_at) * 1000
        if decision == "approved":
            pending.state.approve(pending.interruption)
        else:
            pending.state.reject(
                pending.interruption,
                always_reject=True,
                rejection_message="restart_service was rejected by the human reviewer.",
            )
        try:
            with trace(f"phase6_{pending.experiment}_resume") as agent_trace:
                result = await Runner.run(
                    pending.diagnostics_agent,
                    pending.state,
                    run_config=self._run_config(pending.experiment),
                )
            if result.interruptions:
                raise LlmResponseError("Unexpected additional approval request")
            report = result.final_output_as(DiagnosticReport, raise_if_incorrect_type=True)
            restart_called = any(
                observation.selected_tool == "restart_service"
                for observation in pending.observations
            )
            if decision == "approved" and not restart_called:
                raise LlmResponseError("Approved restart_service was not executed")
            if decision == "rejected" and restart_called:
                raise ApprovalRejectionError("Rejected restart_service was executed")
            return self._result(
                run_id=run_id,
                experiment=pending.experiment,
                state="completed",
                approval=_approval_request(pending.interruption),
                decision=decision,
                report=report,
                observations=pending.observations,
                handoffs=pending.handoffs,
                result=result,
                started_at=pending.started_at,
                approval_wait_ms=approval_wait_ms,
                trace_id=agent_trace.trace_id,
            )
        except (AgentRunError, ApprovalRejectionError, LlmResponseError):
            raise
        except Exception as error:
            raise AgentRunError("Multi-agent approval resume failed") from error
        finally:
            await pending.diagnostics_server.__aexit__(None, None, None)
            await pending.operations_server.__aexit__(None, None, None)

    def _agents(
        self,
        operations_server: RecordingMCPServerStdio,
        diagnostics_server: RecordingMCPServerStdio,
        handoffs: list[HandoffObservation],
    ) -> Agent:
        api_key, model = self._settings.require_openai()
        operations_agent = Agent(
            name=OPERATIONS_AGENT_NAME,
            instructions=OPERATIONS_INSTRUCTIONS,
            mcp_servers=[operations_server],
            model=OpenAIResponsesModel(model, AsyncOpenAI(api_key=api_key)),
            model_settings=ModelSettings(preserve_raw_usage=True),
            output_type=DiagnosticReport,
        )

        def record_handoff(_context: Any) -> None:
            handoffs.append(
                HandoffObservation(
                    from_agent=DIAGNOSTICS_AGENT_NAME,
                    to_agent=OPERATIONS_AGENT_NAME,
                )
            )

        return Agent(
            name=DIAGNOSTICS_AGENT_NAME,
            instructions=DIAGNOSTICS_INSTRUCTIONS,
            mcp_servers=[diagnostics_server],
            handoffs=[
                handoff(
                    operations_agent,
                    tool_name_override="transfer_to_operations_agent",
                    tool_description_override=(
                        "Delegate restart operations to the Operations Agent after diagnosis."
                    ),
                    on_handoff=record_handoff,
                )
            ],
            model=OpenAIResponsesModel(model, AsyncOpenAI(api_key=api_key)),
            model_settings=ModelSettings(preserve_raw_usage=True),
            output_type=DiagnosticReport,
        )

    def _server(
        self,
        observations: list[ToolObservation],
        agent_name: str,
        allowed_tool_names: list[str],
        *,
        require_approval: dict[str, Literal["always", "never"]] | None = None,
    ) -> RecordingMCPServerStdio:
        return RecordingMCPServerStdio(
            params={
                "command": sys.executable,
                "args": ["-m", "mcp_ai_agent_lab.mcp_server"],
                "env": {"BACKEND_BASE_URL": self._settings.backend_base_url},
            },
            observations=observations,
            agent_name=agent_name,
            name=f"{agent_name} MCP Server",
            tool_filter={"allowed_tool_names": allowed_tool_names},
            require_approval=require_approval,
        )

    @staticmethod
    def _question(experiment: Literal["explicit_handoff", "autonomous_decision"]) -> str:
        if experiment == "explicit_handoff":
            return EXPLICIT_HANDOFF_QUESTION
        return AUTONOMOUS_DECISION_QUESTION

    @staticmethod
    def _run_config(experiment: str) -> RunConfig:
        return RunConfig(
            workflow_name=f"phase6_{experiment}",
            trace_include_sensitive_data=False,
        )

    @staticmethod
    def _result(
        *,
        run_id: str,
        experiment: Literal["explicit_handoff", "autonomous_decision"],
        state: Literal["pending_approval", "completed"],
        approval: ApprovalRequest | None,
        decision: Literal["approved", "rejected"] | None,
        report: DiagnosticReport | None,
        observations: list[ToolObservation],
        handoffs: list[HandoffObservation],
        result: Any,
        started_at: float,
        approval_wait_ms: float,
        trace_id: str,
    ) -> MultiAgentRunResult:
        usage = result.context_wrapper.usage
        return MultiAgentRunResult(
            run_id=run_id,
            experiment=experiment,
            state=state,
            approval=approval,
            approval_count=1 if approval else 0,
            approval_decision=decision,
            report=report,
            tool_calls=observations,
            handoffs=handoffs,
            llm_requests=usage.requests,
            usage=_agent_usage(result),
            end_to_end_ms=max((perf_counter() - started_at) * 1000 - approval_wait_ms, 0),
            approval_wait_ms=approval_wait_ms,
            required_evidence=_required_evidence(observations),
            trace=TRACE_RECORDER.observation(trace_id),
            service_status=fixture_state.status(),
        )


def _approval_request(interruption: ToolApprovalItem) -> ApprovalRequest:
    raw_arguments = getattr(interruption, "arguments", "{}")
    try:
        arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    except json.JSONDecodeError as error:
        raise LlmResponseError("Approval request arguments are invalid") from error
    if not isinstance(arguments, dict):
        raise LlmResponseError("Approval request arguments are invalid")
    tool_name = getattr(interruption, "name", None) or interruption.tool_name
    return ApprovalRequest(tool_name=tool_name or "unknown_tool", tool_arguments=arguments)
