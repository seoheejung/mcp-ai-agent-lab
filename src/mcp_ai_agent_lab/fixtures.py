from __future__ import annotations

from .models import LogEntry, ServiceLogs, ServiceMetrics, ServiceStatus

SERVICE_NAME = "order-api"

SERVICE_STATUS = ServiceStatus(
    service=SERVICE_NAME,
    status="degraded",
    checked_at="2026-08-25T09:00:00+09:00",
)

SERVICE_METRICS = ServiceMetrics(
    service=SERVICE_NAME,
    latency_ms=842,
    error_rate=0.073,
    request_count=18420,
    window="last_5_minutes",
)

SERVICE_LOGS = ServiceLogs(
    service=SERVICE_NAME,
    entries=[
        LogEntry(
            timestamp="2026-08-25T08:58:41+09:00",
            level="ERROR",
            message="DB connection pool timeout",
        ),
        LogEntry(
            timestamp="2026-08-25T08:58:12+09:00",
            level="WARN",
            message="Request latency exceeded 800ms",
        ),
    ],
)
