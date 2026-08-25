from __future__ import annotations

import json
from threading import Lock
from time import perf_counter
from typing import Any

from agents import (
    Agent,
    ModelSettings,
    RunConfig,
    Runner,
    function_span,
    function_tool,
    generation_span,
    trace,
)
from agents.models.openai_responses import OpenAIResponsesModel
from agents.tracing import TracingProcessor, add_trace_processor
from openai import AsyncOpenAI
from pydantic import ValidationError

from .config import Settings
from .errors import AgentRunError, LlmResponseError, StructuredOutputError
from .models import (
    DiagnosticComparisonResult,
    DiagnosticExecutionResult,
    DiagnosticReport,
    ResponseUsage,
    ToolObservation,
    TraceObservation,
)
from .runner import REPORT_FORMAT, _response_usage
from .tools import FunctionTools

REQUIRED_TOOL_NAMES = (
    "get_service_status",
    "get_recent_metrics",
    "get_recent_logs",
)
DIAGNOSTICS_AGENT_NAME = "Diagnostics Agent"
DIAGNOSTICS_AGENT_INSTRUCTIONS = (
    "Investigate the user's diagnostics question. Gather service_status, metrics, "
    "and logs with the available read-only function tools before producing the "
    "structured diagnostic report. You choose the tool-call order. Do not use "
    "handoffs, memory, approval, write operations, or any unavailable tool."
)


class TraceRecorder(TracingProcessor):
    def __init__(self) -> None:
        self._lock = Lock()
        self._span_types: dict[str, list[str]] = {}

    def on_trace_start(self, trace: Any) -> None:
        with self._lock:
            self._span_types.setdefault(trace.trace_id, [])

    def on_trace_end(self, trace: Any) -> None:
        return None

    def on_span_start(self, span: Any) -> None:
        return None

    def on_span_end(self, span: Any) -> None:
        with self._lock:
            self._span_types.setdefault(span.trace_id, []).append(span.span_data.type)

    def shutdown(self) -> None:
        with self._lock:
            self._span_types.clear()

    def force_flush(self) -> None:
        return None

    def observation(self, trace_id: str) -> TraceObservation:
        with self._lock:
            span_types = list(self._span_types.get(trace_id, []))
        return TraceObservation(trace_id=trace_id, span_types=span_types)


TRACE_RECORDER = TraceRecorder()
add_trace_processor(TRACE_RECORDER)


class Phase2DiagnosticsRunner:
    def __init__(self, settings: Settings, tools: FunctionTools) -> None:
        self._settings = settings
        self._tools = tools

    async def run(self, question: str) -> DiagnosticComparisonResult:
        return DiagnosticComparisonResult(
            question=question,
            workflow=await self._run_workflow(question),
            agent=await self._run_agent(question),
        )

    async def _run_workflow(self, question: str) -> DiagnosticExecutionResult:
        api_key, model = self._settings.require_openai()
        started_at = perf_counter()
        client = AsyncOpenAI(api_key=api_key)
        with trace("phase2_deterministic_workflow") as workflow_trace:
            with function_span("get_service_status"):
                status = await self._call_tool(
                    "get_service_status", {"service": "order-api"}
                )
            with function_span("get_recent_metrics"):
                metrics = await self._call_tool(
                    "get_recent_metrics", {"service": "order-api"}
                )
            with function_span("get_recent_logs"):
                logs = await self._call_tool(
                    "get_recent_logs", {"service": "order-api", "limit": 10}
                )
            observations = [status, metrics, logs]
            with generation_span(model=model):
                response = await client.responses.create(
                    model=model,
                    instructions=(
                        "Create a concise diagnostic report using all supplied Backend Diagnostics "
                        "evidence. Return only the required JSON schema."
                    ),
                    input=json.dumps(
                        {
                            "question": question,
                            "service_status": status.tool_result,
                            "metrics": metrics.tool_result,
                            "logs": logs.tool_result,
                        }
                    ),
                    text={"format": REPORT_FORMAT},
                )
        report = _validate_report(response.output_text)
        return DiagnosticExecutionResult(
            report=report,
            tool_calls=observations,
            llm_requests=1,
            usage=_response_usage(response),
            end_to_end_ms=(perf_counter() - started_at) * 1000,
            required_evidence=list(REQUIRED_TOOL_NAMES),
            trace=TRACE_RECORDER.observation(workflow_trace.trace_id),
        )

    async def _run_agent(self, question: str) -> DiagnosticExecutionResult:
        api_key, model = self._settings.require_openai()
        observations: list[ToolObservation] = []

        async def execute(name: str, arguments: dict[str, object]) -> dict[str, object]:
            started_at = perf_counter()
            result = await self._tools.execute(name, arguments)
            observations.append(
                ToolObservation(
                    selected_tool=name,
                    tool_arguments=arguments,
                    tool_result=result,
                    tool_latency_ms=(perf_counter() - started_at) * 1000,
                )
            )
            return result

        @function_tool(name_override="get_service_status")
        async def get_service_status(service: str) -> dict[str, object]:
            """Get the current diagnostics status for one service."""
            return await execute("get_service_status", {"service": service})

        @function_tool(name_override="get_recent_metrics")
        async def get_recent_metrics(service: str) -> dict[str, object]:
            """Get recent latency, error-rate, and request-count metrics for one service."""
            return await execute("get_recent_metrics", {"service": service})

        @function_tool(name_override="get_recent_logs")
        async def get_recent_logs(service: str, limit: int) -> dict[str, object]:
            """Get recent error and warning logs for one service."""
            return await execute(
                "get_recent_logs", {"service": service, "limit": limit}
            )

        agent = Agent(
            name=DIAGNOSTICS_AGENT_NAME,
            instructions=DIAGNOSTICS_AGENT_INSTRUCTIONS,
            tools=[get_service_status, get_recent_metrics, get_recent_logs],
            model=OpenAIResponsesModel(model, AsyncOpenAI(api_key=api_key)),
            model_settings=ModelSettings(preserve_raw_usage=True),
            output_type=DiagnosticReport,
        )
        started_at = perf_counter()
        try:
            with trace("phase2_diagnostics_agent") as agent_trace:
                result = await Runner.run(
                    agent,
                    question,
                    run_config=RunConfig(
                        workflow_name="phase2_diagnostics_agent",
                        trace_include_sensitive_data=False,
                    ),
                )
        except Exception as error:
            raise AgentRunError("Diagnostics Agent run failed") from error

        report = result.final_output_as(DiagnosticReport, raise_if_incorrect_type=True)
        required_evidence = _required_evidence(observations)
        if len(required_evidence) != len(REQUIRED_TOOL_NAMES):
            raise LlmResponseError("Diagnostics Agent did not collect all required evidence")
        usage = result.context_wrapper.usage
        return DiagnosticExecutionResult(
            report=report,
            tool_calls=observations,
            llm_requests=usage.requests,
            usage=_agent_usage(result),
            end_to_end_ms=(perf_counter() - started_at) * 1000,
            required_evidence=required_evidence,
            trace=TRACE_RECORDER.observation(agent_trace.trace_id),
        )

    async def _call_tool(
        self, name: str, arguments: dict[str, object]
    ) -> ToolObservation:
        started_at = perf_counter()
        result = await self._tools.execute(name, arguments)
        return ToolObservation(
            selected_tool=name,
            tool_arguments=arguments,
            tool_result=result,
            tool_latency_ms=(perf_counter() - started_at) * 1000,
        )


def _validate_report(output: str) -> DiagnosticReport:
    try:
        return DiagnosticReport.model_validate_json(output)
    except (ValidationError, ValueError) as error:
        raise StructuredOutputError("Model response failed DiagnosticReport validation") from error


def _required_evidence(observations: list[ToolObservation]) -> list[str]:
    called_tools = {observation.selected_tool for observation in observations}
    return [name for name in REQUIRED_TOOL_NAMES if name in called_tools]


def _agent_usage(result: Any) -> ResponseUsage | None:
    raw_responses = result.raw_responses
    if not raw_responses or any(response.raw_usage is None for response in raw_responses):
        return None
    usage = result.context_wrapper.usage
    return ResponseUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
    )
