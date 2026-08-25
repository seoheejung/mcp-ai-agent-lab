# Phase 6. Multi-Agent

## 학습 목표

Diagnostics Agent와 Operations Agent의 Tool 권한을 분리하고, Handoff와 `restart_service`의 Human Approval 재개 흐름을 실제 MCP stdio 실행으로 확인한다.

## 실습

- Agent는 Diagnostics Agent와 Operations Agent 두 개만 구성했다.
- Diagnostics Agent MCP Server에는 `get_service_status`, `get_recent_metrics`, `get_recent_logs`만 노출했다.
- Operations Agent MCP Server에는 `get_service_status`, `restart_service`만 노출했고, `restart_service`는 `always` Human Approval로 설정했다.
- Web Application은 명시적 Handoff와 자율 판단을 별도 시작 버튼으로 제공하며, Handoff, Agent별 Tool Call, 승인 대기와 동일 RunState의 Approve/Reject 재개 결과를 표시한다.
- 두 실제 실험은 각각 시작 전에 `order-api` fixture를 `degraded`로 초기화했다.

## 확인 결과

### 명시적 Handoff 실험

질문: `order-api 상태를 확인한 뒤 재시작 작업을 Operations Agent에게 위임해줘.`

- 실제 Handoff: `Diagnostics Agent -> Operations Agent`
- 승인 전 Diagnostics Agent 실제 Tool Call 순서: `get_service_status`, `get_recent_metrics`, `get_recent_logs`
- 승인 전 Tool arguments: status/metrics는 `{"service":"order-api"}`, logs는 `{"service":"order-api","limit":10}`
- Tool 결과: status `degraded`, metrics `latency_ms=842`, `error_rate=0.073`, `request_count=18420`, logs 2건
- 승인 요청: `restart_service`, arguments `{"service":"order-api"}`. 승인 전 restart Tool Call은 없었다.
- 시작 구간: LLM Requests `3`, Tokens `1393 input / 218 output / 1611 total`, End-to-End `15301.40 ms`, Tool time `3713.25 ms`, `3714.74 ms`, `3717.23 ms`
- Approve 재개: Operations Agent가 `restart_service({"service":"order-api"})`를 호출했고 결과는 `{"service":"order-api","status":"healthy"}`였다. Tool time은 `1526.64 ms`, fixture 상태는 `healthy`였다.
- 완료 누적: LLM Requests `4`, Tokens `2031 input / 397 output / 2428 total`, End-to-End `19531.75 ms`, Approval wait `8222.15 ms`
- Required Evidence: `get_service_status`, `get_recent_metrics`, `get_recent_logs`

### 자율 판단 실험

질문: `order-api의 응답 지연 원인을 조사하고 필요한 조치를 수행해줘.`

- 실제 Handoff: `Diagnostics Agent -> Operations Agent`. 이는 코드로 강제한 결과가 아니라 이 실행에서 모델이 선택한 결과다.
- 승인 전 Diagnostics Agent 실제 Tool Call 순서: `get_service_status`, `get_recent_metrics`, `get_recent_logs`
- Tool arguments: status/metrics는 `{"service":"order-api"}`, logs는 `{"service":"order-api","limit":50}`
- Tool 결과: status `degraded`, metrics `latency_ms=842`, `error_rate=0.073`, `request_count=18420`, logs 2건
- 승인 요청: `restart_service`, arguments `{"service":"order-api"}`. 승인 전 restart Tool Call은 없었다.
- 시작 구간: LLM Requests `3`, Tokens `1435 input / 238 output / 1673 total`, End-to-End `11672.17 ms`, Tool time `3593.46 ms`, `3596.20 ms`, `3600.27 ms`
- Reject 재개: `restart_service`는 호출되지 않았고, fixture 상태는 `degraded`로 유지됐다.
- 완료 누적: LLM Requests `4`, Tokens `2090 input / 452 output / 2542 total`, End-to-End `14719.23 ms`, Approval wait `18899.05 ms`
- Required Evidence: `get_service_status`, `get_recent_metrics`, `get_recent_logs`

### Single Agent와 Multi-Agent 비교

같은 Backend, degraded fixture, MCP stdio, Function Tool 의미, `OPENAI_MODEL` 설정 및 자율 판단 질문으로 기존 Phase 5 단일 Agent를 실제 실행했다. 단일 Agent는 `get_service_status`, `get_recent_metrics`, `get_recent_logs`를 차례로 호출했고, `restart_service` 승인 요청은 만들지 않았다. 최종 `recommended_action`은 `restart_service`였지만 fixture 상태는 `degraded`로 남았다.

| 측정 항목 | Single Agent | Multi-Agent 자율 판단 (Reject) |
| --- | --- | --- |
| Agent 수 | 1 | 2 |
| 권한 | 한 Agent에 Read 및 restart Tool 노출 | Diagnostics는 Read 전용, Operations는 status/restart만 노출 |
| Handoff | 없음 | Diagnostics -> Operations 관측 |
| Tool Calls | status, metrics, logs | status, metrics, logs; restart는 Reject로 미호출 |
| LLM Requests | 2 | 4 |
| Tokens | 947 input / 571 output / 1518 total | 2090 input / 452 output / 2542 total |
| End-to-End Time | 13017.47 ms | 14719.23 ms |
| Approval | 요청 없음 | restart 요청 1건, Reject |

두 실행은 도구 선택과 응답이 모델 실행에 따라 달랐으므로, 이 한 번의 측정만으로 성능이나 품질의 우열은 결론 내리지 않았다.

### Agents SDK Tracing

모든 위 실제 실행에서 Trace가 생성됐다. Trace ID는 민감 정보 노출 방지를 위해 기록하지 않았다.

- 명시적 Handoff 시작: `mcp_tools` 3회, `response` 3회, `function` 4회, `turn` 3회, `handoff`, `agent` 2회, `task`
- 명시적 Handoff Approve 재개: `mcp_tools` 2회, `function`, `response`, `turn`, `agent`, `task`
- 자율 판단 시작: `mcp_tools` 3회, `response` 3회, `function` 4회, `turn` 3회, `handoff`, `agent` 2회, `task`
- 자율 판단 Reject 재개: `mcp_tools` 2회, `response`, `turn`, `agent`, `task`
- Single Agent: `mcp_tools` 2회, `response` 2회, `function` 3회, `turn` 2회, `agent`, `task`

Multi-Agent Trace에는 실제 `handoff` span이 포함됐고, 단일 Agent Trace에는 포함되지 않았다.
