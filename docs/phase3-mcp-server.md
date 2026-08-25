# Phase 3. MCP Server

## 학습 목표

LLM과 Agent 없이 stdio FastMCP Server가 기존 Backend Diagnostics API를 MCP Tool로 제공하고, 독립 FastMCP Client가 Tool Discovery와 Tool Call을 수행하는 흐름을 확인한다.

## 실습

- FastMCP `3.4.7`을 사용했다.
- Transport는 stdio만 사용했다.
- MCP Server는 `get_service_status`, `get_recent_metrics`, `get_recent_logs` 세 Read-only Tool만 제공했다.
- 각 Tool은 HTTPX 기반 기존 Backend Diagnostics API를 호출했다.
- Web Application은 `/api/mcp/verification`을 통해 실제 MCP Discovery와 세 정상 Tool Call 결과를 표시한다.
- LLM, Agent, MCP Resources, MCP Prompts, Streamable HTTP, Human Approval, Handoff, Multi-Agent는 사용하지 않았다.

## 확인 결과

### stdio Tool Discovery와 Schema

실제 stdio Client가 다음 세 Tool을 발견했다.

| Tool | Input Schema | Output Schema |
| --- | --- | --- |
| `get_service_status` | `service`: required string | `service`, `status=degraded`, `checked_at` date-time |
| `get_recent_metrics` | `service`: required string | `service`, `latency_ms` integer ≥ 0, `error_rate` number 0~1, `request_count` integer ≥ 0, `window` |
| `get_recent_logs` | `service`: required string; `limit`: integer, default 10, minimum 1, maximum 100 | `service`, `entries[]` with `timestamp`, `level` (`ERROR` or `WARN`), `message` |

### 정상 Tool Call

| Tool | 실제 Arguments | 실제 Result | Tool 실행 시간 |
| --- | --- | --- | --- |
| `get_service_status` | `{"service":"order-api"}` | `status=degraded`, `checked_at=2026-08-25T09:00:00+09:00` | 1240.0841 ms |
| `get_recent_metrics` | `{"service":"order-api"}` | `latency_ms=842`, `error_rate=0.073`, `request_count=18420`, `window=last_5_minutes` | 1242.8053 ms |
| `get_recent_logs` | `{"service":"order-api","limit":10}` | `ERROR: DB connection pool timeout`; `WARN: Request latency exceeded 800ms` | 1243.2176 ms |

실제 stdio 검증의 전체 실행 시간은 5440.8680 ms였다. LLM과 Agent를 실행하지 않았으므로 LLM Request와 Token Usage는 측정 대상이 아니다.

### 오류 전달

실제 독립 Client 실행에서 다음 오류 경로를 확인했다.

| 조건 | 실제 결과 |
| --- | --- |
| `get_recent_logs`에 `limit: 0` 전달 | `McpToolError` / `mcp_tool_error` |
| `get_service_status`에 `service: unknown-api` 전달 | `McpToolError` / `mcp_tool_error` |
| Backend URL을 `http://127.0.0.1:1`로 설정 | `McpToolError` / `mcp_tool_error` |
| 존재하지 않는 stdio MCP Server 모듈로 연결 | FastMCP SDK `McpError` |
