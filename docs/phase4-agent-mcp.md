# Phase 4. Agent + MCP

## 학습 목표

Phase 2 Diagnostics Agent가 Local Function Tool과 stdio FastMCP Tool을 각각 사용할 수 있게 연결하고, 같은 Backend Diagnostics fixture를 실제 OpenAI Agents SDK 실행으로 비교한다.

## 실습

- `MCPServerStdio`로 `python -m mcp_ai_agent_lab.mcp_server`를 연결했다.
- Local Function과 MCP 모두 같은 Diagnostics Agent 이름, instruction, `DiagnosticReport` output schema, `OPENAI_MODEL` 환경 변수 값, 평가 질문, Backend fixture를 사용했다.
- 연결 방식만 Local Function Tool과 stdio MCP Tool로 달리했다.
- 웹의 `RUN AGENT MCP COMPARISON`은 `POST /api/agent-mcp/comparison`을 호출하고, 두 실행의 결과·도구 호출·usage·시간·필수 증거·trace를 나란히 표시한다.

## 확인 결과

### 실제 비교 실행

평가 질문은 `order-api의 응답이 느려졌어. 원인을 조사해줘.`였고, 실제 FastAPI fixture와 설정된 `OPENAI_MODEL`을 사용했다. 두 실행 모두 성공했고, `order-api`가 `degraded` 상태, 최근 지연 시간 `842 ms`, 오류율 `0.073`, 요청 수 `18,420`, 로그의 `DB connection pool timeout` 및 `Request latency exceeded 800ms`를 받았다. 두 최종 보고서 모두 DB connection pool 고갈 또는 DB 지연을 원인으로 제시하고 `restart_service`를 권고했다.

| 측정 항목 | Local Function | MCP stdio |
| --- | ---: | ---: |
| Success | `true` | `true` |
| Tool Calls | 3 | 3 |
| LLM Requests | 2 | 2 |
| Input Tokens | 871 | 819 |
| Output Tokens | 385 | 375 |
| Total Tokens | 1,256 | 1,194 |
| End-to-End Time | 13,315.2218 ms | 10,084.8971 ms |
| Tool Time 합계 | 7,936.1134 ms | 11,871.2636 ms |
| Required Evidence | 세 도구 모두 | 세 도구 모두 |

한 번의 실제 실행 수치일 뿐이므로 어느 연결 방식이 더 빠르거나 더 낫다는 결론은 내리지 않았다.

### 실제 Tool Calls

Local Function의 실제 호출 순서는 `get_service_status` → `get_recent_metrics` → `get_recent_logs`였다. 실제 arguments는 각각 `{"service":"order-api"}`, `{"service":"order-api"}`, `{"service":"order-api","limit":50}`였다. 개별 Tool Time은 3,960.3771 ms, 2,640.2501 ms, 1,335.4862 ms였다.

MCP stdio의 실제 호출 순서도 `get_service_status` → `get_recent_metrics` → `get_recent_logs`였다. 실제 arguments는 각각 `{"service":"order-api"}`, `{"service":"order-api"}`, `{"service":"order-api","limit":20}`였다. 개별 Tool Time은 3,952.0677 ms, 3,957.3873 ms, 3,961.8086 ms였다.

두 경로 모두 도구 호출 순서와 `limit` 값은 코드에서 고정하거나 유도하지 않았으며, 모델이 도구 호출에서 선택한 실제 값이다.

### Tracing

두 실제 실행에서 Agents SDK trace가 생성됐다. 실제 Trace ID는 생성 여부를 확인했지만 운영 식별자 노출을 피하기 위해 문서에 재기록하지 않았다.

Local Function trace span 종류는 `response`, `function`, `function`, `function`, `turn`, `response`, `turn`, `agent`, `task`였다.

MCP stdio trace span 종류는 `mcp_tools`, `response`, `function`, `function`, `function`, `turn`, `mcp_tools`, `response`, `turn`, `agent`, `task`였다.

### 오류 전달

- 실제로 Backend FastAPI 주소를 연결 불가 주소로 설정한 Local Function Agent 실행은 필요한 증거를 수집하지 못해 `LlmResponseError`로 끝났다.
- 같은 조건의 실제 MCP Agent 실행에서는 FastMCP Tool이 Backend 연결 실패를 반환했고, Agent 실행은 `AgentRunError`이며 원인은 `LlmResponseError`로 확인됐다.
- 실제 `MCPServerStdio`에 즉시 종료되는 stdio 프로세스를 연결했을 때 SDK는 `McpError`를 반환했다.
