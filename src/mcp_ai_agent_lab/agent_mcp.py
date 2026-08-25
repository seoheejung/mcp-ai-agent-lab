from __future__ import annotations

import json
import sys
from time import perf_counter
from typing import Any

from agents import Agent, ModelSettings, RunConfig, Runner, function_tool, trace
from agents.mcp import MCPServerStdio
from agents.models.openai_responses import OpenAIResponsesModel
from openai import AsyncOpenAI

from .agent_loop import (
    DIAGNOSTICS_AGENT_INSTRUCTIONS,
    DIAGNOSTICS_AGENT_NAME,
    REQUIRED_TOOL_NAMES,
    TRACE_RECORDER,
    _agent_usage,
    _required_evidence,
)
from .config import Settings
from .errors import (
    AgentRunError,
    ApplicationError,
    LlmResponseError,
    McpConnectionError,
    McpToolError,
)
from .models import (
    AgentMcpComparisonResult,
    AgentMcpExecutionResult,
    DiagnosticReport,
    ToolObservation,
)
from .tools import FunctionTools


class RecordingMCPServerStdio(MCPServerStdio):
    def __init__(
        self,
        *args: Any,
        observations: list[ToolObservation],
        agent_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._observations = observations
        self._agent_name = agent_name

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None,
        meta: dict[str, Any] | None = None,
    ) -> Any:
        started_at = perf_counter()
        result = await super().call_tool(tool_name, arguments, meta)
        structured_content = getattr(result, "structuredContent", None)
        if not isinstance(structured_content, dict):
            raise McpToolError("MCP tool did not return structured content")
        self._observations.append(
            ToolObservation(
                selected_tool=tool_name,
                tool_arguments=arguments or {},
                tool_result=structured_content,
                tool_latency_ms=(perf_counter() - started_at) * 1000,
                agent_name=self._agent_name,
            )
        )
        return result


class Phase4AgentMcpRunner:
    def __init__(self, settings: Settings, tools: FunctionTools) -> None:
        self._settings = settings
        self._tools = tools

    async def run(self, question: str) -> AgentMcpComparisonResult:
        return AgentMcpComparisonResult(
            question=question,
            local_function=await self._run_local_function(question),
            mcp=await self._run_mcp(question),
        )

    async def _run_local_function(self, question: str) -> AgentMcpExecutionResult:
        observations: list[ToolObservation] = []
        agent = self._agent(tools=self._local_tools(observations))
        return await self._run_agent(
            agent,
            question,
            observations,
            "phase4_local_function_agent",
        )

    async def _run_mcp(self, question: str) -> AgentMcpExecutionResult:
        observations: list[ToolObservation] = []
        server = RecordingMCPServerStdio(
            params={
                "command": sys.executable,
                "args": ["-m", "mcp_ai_agent_lab.mcp_server"],
                "env": {"BACKEND_BASE_URL": self._settings.backend_base_url},
            },
            observations=observations,
            name="Backend Diagnostics MCP Server",
        )
        try:
            async with server:
                agent = self._agent(mcp_servers=[server])
                return await self._run_agent(
                    agent,
                    question,
                    observations,
                    "phase4_mcp_agent",
                )
        except ApplicationError:
            raise
        except Exception as error:
            raise McpConnectionError("Unable to connect to Backend Diagnostics MCP Server") from error

    def _agent(
        self,
        *,
        tools: list[Any] | None = None,
        mcp_servers: list[MCPServerStdio] | None = None,
    ) -> Agent:
        api_key, model = self._settings.require_openai()
        return Agent(
            name=DIAGNOSTICS_AGENT_NAME,
            instructions=DIAGNOSTICS_AGENT_INSTRUCTIONS,
            tools=tools or [],
            mcp_servers=mcp_servers or [],
            model=OpenAIResponsesModel(model, AsyncOpenAI(api_key=api_key)),
            model_settings=ModelSettings(preserve_raw_usage=True),
            output_type=DiagnosticReport,
        )

    def _local_tools(self, observations: list[ToolObservation]) -> list[Any]:
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

        return [get_service_status, get_recent_metrics, get_recent_logs]

    async def _run_agent(
        self,
        agent: Agent,
        question: str,
        observations: list[ToolObservation],
        workflow_name: str,
    ) -> AgentMcpExecutionResult:
        started_at = perf_counter()
        try:
            with trace(workflow_name) as agent_trace:
                result = await Runner.run(
                    agent,
                    question,
                    run_config=RunConfig(
                        workflow_name=workflow_name,
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
        return AgentMcpExecutionResult(
            success=True,
            report=report,
            tool_calls=observations,
            llm_requests=usage.requests,
            usage=_agent_usage(result),
            end_to_end_ms=(perf_counter() - started_at) * 1000,
            required_evidence=required_evidence,
            trace=TRACE_RECORDER.observation(agent_trace.trace_id),
        )
