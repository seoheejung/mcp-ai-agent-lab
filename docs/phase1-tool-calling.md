# Phase 1. Tool Calling

## 학습 목표

OpenAI Responses API의 Function Tool Calling으로 Backend Diagnostics API를 호출하고, Tool 결과를 사용한 Structured Output과 Streaming 응답을 실제 실행으로 확인한다.

## 실습

- `order-api` 상태 질문에서 `get_service_status` Function Tool 선택
- 성능 지표 질문에서 `get_recent_metrics` Function Tool 선택
- 오류 로그 질문에서 `get_recent_logs` Function Tool 선택
- 각 Tool이 HTTPX를 통해 FastAPI Diagnostics API를 호출
- Tool 결과를 `function_call_output`으로 전달한 뒤 `DiagnosticReport` Structured Output 검증
- Responses API Streaming 이벤트 수집
- `unknown-api` Tool 호출의 404 오류 전달 확인

## 확인 결과

### Responses API Function Tool Calling

| 질문 | 선택된 Tool | Function Call Arguments | HTTPX Tool 결과 | Tool 실행 시간 | Usage |
| --- | --- | --- | --- | ---: | --- |
| `order-api 상태를 확인해줘.` | `get_service_status` | `{"service":"order-api"}` | `{"service":"order-api","status":"degraded","checked_at":"2026-08-25T09:00:00+09:00"}` | 1206.8168999994668 ms | input 426, output 125, total 551 |
| `order-api의 최근 성능 지표를 확인해줘.` | `get_recent_metrics` | `{"service":"order-api"}` | `{"service":"order-api","latency_ms":842,"error_rate":0.073,"request_count":18420,"window":"last_5_minutes"}` | 1176.4492000002065 ms | input 433, output 138, total 571 |
| `order-api의 최근 오류 로그를 확인해줘.` | `get_recent_logs` | `{"service":"order-api","limit":100}` | `{"service":"order-api","entries":[{"timestamp":"2026-08-25T08:58:41+09:00","level":"ERROR","message":"DB connection pool timeout"},{"timestamp":"2026-08-25T08:58:12+09:00","level":"WARN","message":"Request latency exceeded 800ms"}]}` | 1179.4124000007287 ms | input 474, output 149, total 623 |

각 실행에서 Tool 결과를 `function_call_output`으로 전달한 후 응답을 `DiagnosticReport`로 검증했다.

| Tool | Structured Output 실제 결과 |
| --- | --- |
| `get_service_status` | `service=order-api`, `recommended_action=restart_service`, evidence에 `degraded` 상태 포함 |
| `get_recent_metrics` | `service=order-api`, `summary=Elevated latency and error rate detected over the last 5 minutes.`, evidence: `Latency: 842 ms`, `Error rate: 7.3%`, `Request count: 18,420`, `recommended_action=restart_service` |
| `get_recent_logs` | `service=order-api`, `summary=Database connection pool timeout detected, with elevated request latency.`, evidence에 `DB connection pool timeout` 및 `Request latency exceeded 800ms` 포함, `recommended_action=restart_service` |

### 오류 경로

`Check unknown-api status.` 요청은 실제 Tool 실행 경로에서 HTTP 404를 반환했다.

### Streaming

Streaming 확인 요청에서 수집한 실제 이벤트 순서는 다음과 같다.

```text
response.created
response.in_progress
response.output_item.added
response.content_part.added
response.output_text.delta
response.output_text.delta
response.output_text.delta
response.output_text.delta
response.output_text.done
response.content_part.done
response.output_item.done
response.completed
```

`response.output_text.delta`와 `response.completed` 이벤트를 모두 확인했다.
