# Phase 2. Agent Loop

## 학습 목표

동일한 Backend Diagnostics Fixture와 Function Tool을 사용해 고정 순서의 Deterministic Workflow와 모델이 Tool 호출 순서를 선택하는 Diagnostics Agent를 실제 실행하고, 실행 흐름·Usage·Tracing을 비교한다.

## 실습

- 평가 질문: `order-api의 응답이 느려졌어. 원인을 조사해줘.`
- 실행 조건: 실제 FastAPI 앱, 동일한 `order-api` Fixture, 동일한 세 Read-only Function Tool, 실행 환경의 동일한 `OPENAI_MODEL`
- Required Evidence: `service_status`, `metrics`, `logs`
- Workflow 고정 순서: `get_service_status` → `get_recent_metrics` → `get_recent_logs` → LLM
- Agent Tool 순서: 코드에서 고정하지 않고 Agent Loop가 선택

## 확인 결과

### 공통 최종 결과

두 실행 모두 구조화된 `DiagnosticReport`를 반환했다.

- `service`: `order-api`
- 근거: `status=degraded`, `latency_ms=842`, `error_rate=0.073`, `request_count=18420`, `DB connection pool timeout`, `Request latency exceeded 800ms`
- Required Evidence: 세 항목 모두 수집
- Workflow `recommended_action`: `restart_service`
- Agent `recommended_action`: `none`

### 실제 Tool Calls와 결과

| 실행 | 호출 순서 | 실제 Arguments | 실제 Result | Tool 실행 시간 |
| --- | --- | --- | --- | --- |
| Workflow | `get_service_status` | `{"service":"order-api"}` | `status=degraded`, `checked_at=2026-08-25T09:00:00+09:00` | 1221.8905 ms |
| Workflow | `get_recent_metrics` | `{"service":"order-api"}` | `latency_ms=842`, `error_rate=0.073`, `request_count=18420`, `window=last_5_minutes` | 1200.5601 ms |
| Workflow | `get_recent_logs` | `{"service":"order-api","limit":10}` | `ERROR: DB connection pool timeout`; `WARN: Request latency exceeded 800ms` | 1176.1053 ms |
| Agent | `get_service_status` | `{"service":"order-api"}` | `status=degraded`, `checked_at=2026-08-25T09:00:00+09:00` | 3659.0542 ms |
| Agent | `get_recent_metrics` | `{"service":"order-api"}` | `latency_ms=842`, `error_rate=0.073`, `request_count=18420`, `window=last_5_minutes` | 2480.7532 ms |
| Agent | `get_recent_logs` | `{"service":"order-api","limit":100}` | `ERROR: DB connection pool timeout`; `WARN: Request latency exceeded 800ms` | 1211.2701 ms |

Workflow는 구현된 고정 순서가 실제 실행에서도 유지됐다. Agent의 실제 호출 순서는 이번 실행에서 `get_service_status` → `get_recent_metrics` → `get_recent_logs`였으며, 로그 조회의 `limit`은 Agent가 `100`으로 선택했다. 이 순서는 코드에서 고정하거나 유도하지 않았다.

### Workflow와 Agent 비교

| 항목 | Deterministic Workflow | Diagnostics Agent |
| --- | ---: | ---: |
| Tool Calls | 3 | 3 |
| LLM Requests | 1 | 2 |
| input_tokens | 337 | 870 |
| output_tokens | 210 | 321 |
| total_tokens | 547 | 1191 |
| 전체 실행 시간 | 8028.9780 ms | 9522.9167 ms |
| Tool 실행 시간 합계 | 3598.5559 ms | 7351.0775 ms |
| Required Evidence | `service_status`, `metrics`, `logs` | `service_status`, `metrics`, `logs` |

### Agents SDK Tracing

실제 실행에서 두 Trace가 생성됐고, Trace Recorder가 종료된 span 종류를 수집했다. Trace ID와 span은 mock 값이 아니다.

| 실행 | Trace ID | 실제 span 종류 |
| --- | --- | --- |
| Workflow | `trace_775ed130029c4241b7d971d4a55b93bd` | `function`, `function`, `function`, `generation` |
| Agent | `trace_2c37edf9dbd347c2b4ba4f1ba1b0e87b` | `response`, `function`, `function`, `function`, `turn`, `response`, `turn`, `agent`, `task` |
