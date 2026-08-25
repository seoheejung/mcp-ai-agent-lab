# Phase 5. Human Approval

## 학습 목표

`restart_service` Write Tool에만 Human Approval을 적용하고, 승인 요청으로 중단된 Agent 실행을 Web UI의 결정으로 같은 `RunState`에서 재개한다.

## 실습

- FastAPI에 `POST /services/{service}/restart`를 추가했다. 실제 프로세스나 Docker를 재시작하지 않고 fixture 상태만 `degraded`에서 `healthy`로 바꾼다.
- FastMCP stdio Server에 `restart_service` Tool을 추가했다. 기존 세 Read Tool은 유지했다.
- `MCPServerStdio(require_approval={"restart_service": "always"})`로 Write Tool만 승인 대상으로 설정했다.
- Agent가 승인 요청에서 중단하면 `RunState`와 MCP stdio 연결을 보관한다. Web UI의 Approve 또는 Reject 요청은 같은 `RunState`를 `approve()` 또는 `reject()`한 뒤 재개한다.
- 새 실행마다 fixture 상태를 `degraded`로 초기화한다.

## 확인 결과

### 실제 Approve 실행

초기 실행은 fixture `degraded`에서 시작했다. 모델은 `get_service_status`, `get_recent_metrics`, `get_recent_logs`를 호출한 뒤 `restart_service({"service":"order-api"})` 승인 요청으로 중단했다. 중단 시점의 Tool Calls에는 `restart_service`가 없었고, 상태 조회도 `degraded`였다.

Web API의 Approve 결정으로 동일 RunState를 재개한 뒤 `restart_service`가 한 번 실행됐다. Tool Result는 `{"service":"order-api","status":"healthy"}`였고, 재개 후 상태 조회도 `healthy`였다. 최종 보고서는 DB connection pool 고갈 가능성을 진단하고 재시작 후 `healthy` 복구를 기록했다.

| 측정 항목 | 승인 요청 전 | Approve 재개 완료 |
| --- | ---: | ---: |
| LLM Requests | 2 | 3 |
| Input Tokens | 900 | 1,543 |
| Output Tokens | 143 | 281 |
| Total Tokens | 1,043 | 1,824 |
| End-to-End Time | 12,470.0601 ms | 17,021.1084 ms |
| Approval Wait | 0 ms | 5,738.0223 ms |
| Approval Count | 1 | 1 |
| restart_service Tool Calls | 0 | 1 |
| Fixture Status | `degraded` | `healthy` |

Read Tool의 실제 arguments는 status와 metrics에 `{"service":"order-api"}`, logs에 `{"service":"order-api","limit":20}`였다. Read Tool 실행 시간은 4,336.7196 ms, 4,342.2847 ms, 4,344.6233 ms였고, 승인 후 `restart_service` 실행 시간은 1,195.2240 ms였다.

### 실제 Reject 실행

Approve 실험 후 새 실행을 시작했을 때 fixture가 다시 `degraded`로 초기화된 것을 확인했다. 이 실행도 세 Read Tool 뒤 `restart_service({"service":"order-api"})` 승인 요청으로 중단했고, 거절 전 상태는 `degraded`였다.

Web API의 Reject 결정으로 같은 RunState를 재개한 결과, `restart_service` Tool Calls는 0개였고 fixture 최종 상태는 `degraded`로 유지됐다.

| 측정 항목 | 승인 요청 전 | Reject 재개 완료 |
| --- | ---: | ---: |
| LLM Requests | 2 | 3 |
| Input Tokens | 896 | 1,545 |
| Output Tokens | 150 | 378 |
| Total Tokens | 1,046 | 1,923 |
| End-to-End Time | 11,837.8902 ms | 17,586.8578 ms |
| Approval Wait | 0 ms | 8,210.3778 ms |
| Approval Count | 1 | 1 |
| restart_service Tool Calls | 0 | 0 |
| Fixture Status | `degraded` | `degraded` |

### Tracing

실제 Approve 중단 실행의 span 종류는 `mcp_tools`, `response`, `function`, `function`, `function`, `turn`, `mcp_tools`, `response`, `function`, `turn`, `agent`, `task`였다. Approve 재개 실행은 `mcp_tools`, `function`, `mcp_tools`, `response`, `turn`, `agent`, `task`였다.

실제 Reject 재개 실행의 span 종류는 `mcp_tools`, `mcp_tools`, `response`, `turn`, `agent`, `task`였다. 각 실행에서 Agents SDK Trace ID가 생성된 것을 확인했지만 운영 식별자 노출을 피하기 위해 문서에 재기록하지 않았다.
