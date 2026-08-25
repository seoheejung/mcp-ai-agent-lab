# Phase 2. Agent Loop 작업 지침

## 목적

Phase 1의 Backend와 Function Tool을 유지한 상태에서 Agent Loop만 추가한다.

Deterministic Workflow와 Agent 실행의 제어권 차이 비교가 목적이다.

## 선행 조건

Phase 1 구현·검증 완료 상태 확인.

Phase 1 Fixture, Backend API, Function Tool 의미 변경 금지.

## 구현 범위

- OpenAI Agents SDK Python 도입
- Web Application 진단 실행 화면 연결
- Deterministic Workflow
- Diagnostics Agent
- Agent Loop
- Structured Agent Output
- Usage 측정
- Tracing
- Workflow와 Agent 비교
- Agent 오류 경로 검증

## Agent Tool

Phase 1 Function Tool 재사용:

- `get_service_status`
- `get_recent_metrics`
- `get_recent_logs`

## 비교 구조

Workflow:

`status → metrics → logs → LLM`

Agent:

`Goal → Agent → Tool → Result → 후속 행동`

Agent의 Tool 호출 순서를 코드에서 고정하지 않는다.

## 고정 평가 질문

`order-api의 응답이 느려졌어. 원인을 조사해줘.`

Required Evidence:

- service\_status
- metrics
- logs

Tool 호출 순서는 성공 기준으로 고정하지 않는다.

## 비교 측정

- Success
- Tool Calls
- LLM Requests
- Input Tokens
- Output Tokens
- Total Tokens
- End-to-End Time
- Required Evidence

## 오류 검증

- 404 Tool Result
- FastAPI 연결 실패
- Tool 실행 오류 후 Agent 처리

## 범위 제외

- FastMCP
- MCP Client
- MCP Server
- Human Approval
- Write Tool
- Handoff
- Multi-Agent
- Memory

## 완료 조건

Workflow와 Agent의 실제 실행 흐름을 비교하고 결과를 확인한 경우에만 완료.

실제 검증 완료 후 `docs/phase2-agent-loop.md` 작성.