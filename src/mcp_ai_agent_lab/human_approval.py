from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from agents import Agent, ModelSettings, RunConfig, RunState, Runner, trace
from agents.items import ToolApprovalItem
from agents.models.openai_responses import OpenAIResponsesModel
from openai import AsyncOpenAI

from .agent_loop import (
    DIAGNOSTICS_AGENT_NAME,
    REQUIRED_TOOL_NAMES,
    TRACE_RECORDER,
    _agent_usage,
    _required_evidence,
)
from .agent_mcp import RecordingMCPServerStdio
from .config import Settings
from .errors import (
    AgentRunError,
    ApprovalRejectionError,
    LlmResponseError,
    McpConnectionError,
)
from .fixtures import fixture_state
from .models import ApprovalRequest, ApprovalRunResult, DiagnosticReport, ToolObservation

PHASE5_QUESTION = "order-api의 응답이 느려졌어. 원인을 조사한 뒤 재시작해줘."
PHASE5_INSTRUCTIONS = (
    "Investigate the user's diagnostics question. Gather service status, metrics, and logs "
    "with the available read-only tools before acting. When the evidence shows the service "
    "is degraded and the user asks for a restart, call restart_service. It requires human "
    "approval. After the tool outcome, produce the structured diagnostic report."
)


@dataclass
class PendingApprovalRun:
    agent: Agent
    server: RecordingMCPServerStdio
    state: RunState
    interruption: ToolApprovalItem
    observations: list[ToolObservation]
    started_at: float
    paused_at: float


class Phase5HumanApprovalRunner:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pending_runs: dict[str, PendingApprovalRun] = {}

    async def start(self, question: str = PHASE5_QUESTION) -> ApprovalRunResult:
        fixture_state.reset()
        observations: list[ToolObservation] = []
        server = self._server(observations)
        started_at = perf_counter()
        try:
            await server.__aenter__()
            agent = self._agent(server)
            with trace("phase5_human_approval") as agent_trace:
                result = await Runner.run(
                    agent,
                    question,
                    run_config=self._run_config(),
                )
            if not result.interruptions:
                raise LlmResponseError("Diagnostics Agent did not request restart approval")

            interruption = result.interruptions[0]
            request = _approval_request(interruption)
            if request.tool_name != "restart_service":
                raise LlmResponseError("Unexpected tool approval request")

            run_id = uuid4().hex
            self._pending_runs[run_id] = PendingApprovalRun(
                agent=agent,
                server=server,
                state=result.to_state(),
                interruption=interruption,
                observations=observations,
                started_at=started_at,
                paused_at=perf_counter(),
            )
            return self._result(
                run_id=run_id,
                state="pending_approval",
                approval=request,
                decision=None,
                report=None,
                observations=observations,
                result=result,
                started_at=started_at,
                approval_wait_ms=0,
                trace_id=agent_trace.trace_id,
            )
        except (AgentRunError, LlmResponseError):
            await server.__aexit__(None, None, None)
            raise
        except Exception as error:
            await server.__aexit__(None, None, None)
            raise McpConnectionError("Unable to start Backend Diagnostics MCP Server") from error

    async def resume(
        self,
        run_id: str,
        decision: Literal["approved", "rejected"],
    ) -> ApprovalRunResult:
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
            with trace("phase5_human_approval_resume") as agent_trace:
                result = await Runner.run(
                    pending.agent,
                    pending.state,
                    run_config=self._run_config(),
                )
            if result.interruptions:
                raise LlmResponseError("Diagnostics Agent requested an unexpected additional approval")
            report = result.final_output_as(DiagnosticReport, raise_if_incorrect_type=True)
            required_evidence = _required_evidence(pending.observations)
            if len(required_evidence) != len(REQUIRED_TOOL_NAMES):
                raise LlmResponseError("Diagnostics Agent did not collect all required evidence")
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
                state="completed",
                approval=_approval_request(pending.interruption),
                decision=decision,
                report=report,
                observations=pending.observations,
                result=result,
                started_at=pending.started_at,
                approval_wait_ms=approval_wait_ms,
                trace_id=agent_trace.trace_id,
            )
        except (AgentRunError, ApprovalRejectionError, LlmResponseError):
            raise
        except Exception as error:
            raise AgentRunError("Diagnostics Agent approval resume failed") from error
        finally:
            await pending.server.__aexit__(None, None, None)

    def _server(
        self,
        observations: list[ToolObservation],
    ) -> RecordingMCPServerStdio:
        return RecordingMCPServerStdio(
            params={
                "command": sys.executable,
                "args": ["-m", "mcp_ai_agent_lab.mcp_server"],
                "env": {"BACKEND_BASE_URL": self._settings.backend_base_url},
            },
            observations=observations,
            name="Backend Diagnostics MCP Server",
            require_approval={"restart_service": "always"},
        )

    def _agent(self, server: RecordingMCPServerStdio) -> Agent:
        api_key, model = self._settings.require_openai()
        return Agent(
            name=DIAGNOSTICS_AGENT_NAME,
            instructions=PHASE5_INSTRUCTIONS,
            mcp_servers=[server],
            model=OpenAIResponsesModel(model, AsyncOpenAI(api_key=api_key)),
            model_settings=ModelSettings(preserve_raw_usage=True),
            output_type=DiagnosticReport,
        )

    @staticmethod
    def _run_config() -> RunConfig:
        return RunConfig(
            workflow_name="phase5_human_approval",
            trace_include_sensitive_data=False,
        )

    @staticmethod
    def _result(
        *,
        run_id: str,
        state: Literal["pending_approval", "completed"],
        approval: ApprovalRequest,
        decision: Literal["approved", "rejected"] | None,
        report: DiagnosticReport | None,
        observations: list[ToolObservation],
        result: Any,
        started_at: float,
        approval_wait_ms: float,
        trace_id: str,
    ) -> ApprovalRunResult:
        usage = result.context_wrapper.usage
        return ApprovalRunResult(
            run_id=run_id,
            state=state,
            approval=approval,
            approval_count=1,
            approval_decision=decision,
            report=report,
            tool_calls=observations,
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
