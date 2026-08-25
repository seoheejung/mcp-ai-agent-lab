# Phase 6. Multi-Agent 작업 지침

## 목적

Agent별 역할과 Tool 권한 분리 및 Handoff 검증.

Multi-Agent의 추가 복잡성과 권한 분리 효과 비교.

## 선행 조건

Phase 5 Human Approval 검증 완료.

Approval 정책 유지.

## Agent 구성

Agent는 정확히 2개만 사용.

### Diagnostics Agent

역할:

- 서비스 상태 분석
- Metric 분석
- Log 분석
- 장애 원인 정리
- Operations 작업 필요성 판단

Tool:

- `get_service_status`
- `get_recent_metrics`
- `get_recent_logs`

권한:

Read Only

`restart_service` 제공 금지.

### Operations Agent

역할:

- 승인된 상태 변경 수행
- 변경 결과 확인

Tool:

- `get_service_status`
- `restart_service`

권한:

Read + Human-approved Write

## 구현 범위

- Diagnostics Agent
- Operations Agent
- Web Application Handoff·Approval 상태 표시
- Agent별 Tool 분리
- Diagnostics → Operations Handoff
- 기존 Human Approval 유지
- Single Agent 비교
- Usage
- Tracing

## Handoff 기능 검증

질문:

`order-api 상태를 확인한 뒤 재시작 작업을 Operations Agent에게 위임해줘.`

목적:

Diagnostics Agent

→ Handoff

→ Operations Agent

Handoff 자체를 재현 가능하게 검증.

## Agent 판단 관찰

질문:

`order-api의 응답 지연 원인을 조사하고 필요한 조치를 수행해줘.`

목적:

진단 결과 기반 자율 Handoff 여부 관찰.

이 결과는 필수 Handoff 성공 기준으로 사용하지 않는다.

## Single vs Multi-Agent 비교

측정:

- Agent 수
- Tool 권한 범위
- Handoff
- Write Tool 노출 범위
- Approval
- LLM Requests
- Tokens
- Tool Calls
- End-to-End Time
- Trace Complexity

Multi-Agent가 더 좋다는 사전 결론 금지.

평가 질문:

`역할·권한 분리 효과가 추가 Agent 호출과 실행 복잡성을 감수할 만큼 의미가 있었는가?`

## 범위 제외

- Agent 3개 이상
- Manager Agent
- Agents as Tools
- Parallel Agents
- Agent Swarm
- Agent Debate
- Agent Voting
- Memory
- RAG

## 완료 조건

- 두 Agent 역할 분리
- Tool 권한 분리
- Handoff 성공
- Approval 유지
- Single vs Multi-Agent 실제 비교

완료 후 `docs/phase6-multi-agent.md` 작성.
