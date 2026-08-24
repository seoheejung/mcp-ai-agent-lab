from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ServiceStatus(StrictModel):
    service: str
    status: Literal["degraded"]
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


class StreamingCheckResult(StrictModel):
    event_types: list[str]
