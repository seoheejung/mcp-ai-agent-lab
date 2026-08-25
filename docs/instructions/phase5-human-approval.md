# Phase 5. Human Approval 작업 지침

## 목적

Read Tool과 Write Tool의 권한 차이와 Human Approval 흐름 검증.

실제 운영 인프라가 아닌 Fixture 상태만 변경.

## 선행 조건

Phase 4 Agent + MCP 검증 완료.

기존 Read Tool 동작 유지.

## 추가 Backend API

`POST /services/{service}/restart`

## 추가 MCP Tool

`restart_service`

## Tool 정책

Read Tool:

- `get_service_status`
- `get_recent_metrics`
- `get_recent_logs`

승인 불필요.

Write Tool:

- `restart_service`

승인 필수.

## 구현 범위

- Restart Fixture 상태 변경
- MCP Write Tool
- `MCPServerStdio` Tool별 Approval
- Agent Run interruption
- `RunState`
- Approve
- Reject
- Resume
- 상태 재조회
- Usage
- Trace

## Approve 검증

Web Application에 Approval 요청 표시
→ Web UI에서 Approve

`degraded`

→ restart 요청

→ Approval interruption

→ Approve

→ Tool 실행

→ `healthy`

→ 상태 재조회

## Reject 검증

Web Application에 Approval 요청 표시
→ Web UI에서 Reject

`degraded`

→ restart 요청

→ Approval interruption

→ Reject

→ Tool 미실행

→ `degraded` 유지

각 실험 전 Fixture 상태 초기화.

## 측정

- LLM Requests
- Tokens
- Tool Calls
- Approval Count
- Approval Decision
- End-to-End Time

사람의 실제 승인 대기 시간은 Agent 처리 시간과 분리.

## 범위 제외

- 자동 승인
- RBAC
- OAuth
- 실제 Docker Restart
- Kubernetes
- Multi-Agent

## 완료 조건

Approve와 Reject 두 경로 모두 실제 실행 검증.

한 경로만 성공한 경우 Phase 완료 처리 금지.

완료 후 `docs/phase5-human-approval.md` 작성.