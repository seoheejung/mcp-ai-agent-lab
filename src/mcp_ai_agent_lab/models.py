from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ServiceStatus(StrictModel):
    service: str
    status: Literal["degraded", "healthy"]
    checked_at: datetime


class ServiceMetrics(StrictModel):
    service: str
    latency_ms: int = Field(ge=0)
    error_rate: float = Field(ge=0, le=1)
    request_count: int = Field(ge=0)
    window: str


class LogEntry(StrictModel):
    timestamp: datetime
    level: Literal["ERROR", "WARN"]
    message: str


class ServiceLogs(StrictModel):
    service: str
    entries: list[LogEntry]


class RestartResult(StrictModel):
    service: str
    status: Literal["healthy"]


class DiagnosticReport(StrictModel):
    service: str
    summary: str
    evidence: list[str]
    recommended_action: Literal["none", "restart_service"]


class ResponseUsage(StrictModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ToolObservation(StrictModel):
    selected_tool: str
    tool_arguments: dict[str, object]
    tool_result: dict[str, object]
    tool_latency_ms: float = Field(ge=0)


class DiagnosticRunResult(StrictModel):
    report: DiagnosticReport
    observation: ToolObservation
    usage: ResponseUsage | None


class TraceObservation(StrictModel):
    trace_id: str
    span_types: list[str]


class DiagnosticExecutionResult(StrictModel):
    report: DiagnosticReport
    tool_calls: list[ToolObservation]
    llm_requests: int
    usage: ResponseUsage | None
    end_to_end_ms: float = Field(ge=0)
    required_evidence: list[str]
    trace: TraceObservation | None


class DiagnosticComparisonResult(StrictModel):
    question: str
    workflow: DiagnosticExecutionResult
    agent: DiagnosticExecutionResult


class StreamingCheckResult(StrictModel):
    event_types: list[str]


class McpToolDefinition(StrictModel):
    name: str
    description: str | None
    input_schema: dict[str, object]
    output_schema: dict[str, object]


class McpToolCallResult(StrictModel):
    selected_tool: str
    tool_arguments: dict[str, object]
    tool_result: dict[str, object]
    tool_latency_ms: float = Field(ge=0)


class McpVerificationResult(StrictModel):
    tools: list[McpToolDefinition]
    tool_calls: list[McpToolCallResult]
    end_to_end_ms: float = Field(ge=0)


class AgentMcpExecutionResult(DiagnosticExecutionResult):
    success: bool


class AgentMcpComparisonResult(StrictModel):
    question: str
    local_function: AgentMcpExecutionResult
    mcp: AgentMcpExecutionResult


class ApprovalRequest(StrictModel):
    tool_name: str
    tool_arguments: dict[str, object]


class ApprovalRunResult(StrictModel):
    run_id: str
    state: Literal["pending_approval", "completed"]
    approval: ApprovalRequest | None
    approval_count: int = Field(ge=0)
    approval_decision: Literal["approved", "rejected"] | None
    report: DiagnosticReport | None
    tool_calls: list[ToolObservation]
    llm_requests: int = Field(ge=0)
    usage: ResponseUsage | None
    end_to_end_ms: float = Field(ge=0)
    approval_wait_ms: float = Field(ge=0)
    required_evidence: list[str]
    trace: TraceObservation | None
    service_status: ServiceStatus
