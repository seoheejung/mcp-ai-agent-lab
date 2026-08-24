# Phase 1. Tool Calling 작업 지침

## 목적

`.project/plan.md`의 Phase 1 범위만 구현·검증한다.

LLM의 Function Tool 선택과 실행 흐름 이해가 목적이다.

Agent, MCP 관련 기능은 구현하지 않는다.

## 구현 범위

- Python 3.13.14 프로젝트 초기화
- uv 기반 패키지 관리
- FastAPI Backend Diagnostics API
- Web Application 기본 화면
- HTML·CSS·JavaScript Frontend
- 사용자 질문 입력과 실행 결과 표시
- Backend Fixture
- Pydantic 데이터 모델
- HTTPX 기반 Backend Client
- Function Tool 3개
- OpenAI Responses API Tool Calling
- Structured Output
- Streaming 기본 검증
- Usage 확인
- 정상·오류 경로 검증
- pytest 기반 테스트

## Backend API

- `GET /services/{service}/status`
- `GET /services/{service}/metrics`
- `GET /services/{service}/logs`

`restart` API 구현 금지.

## Function Tool

- `get_service_status`
- `get_recent_metrics`
- `get_recent_logs`

Tool은 HTTPX를 통해 FastAPI 호출.

## 고정 서비스

`order-api`

Fixture는 Phase 1에서 실제 값을 확정한 뒤 이후 Phase에서 유지.

## 검증 입력

- `order-api 상태를 확인해줘.`
- `order-api의 최근 성능 지표를 확인해줘.`
- `order-api의 최근 오류 로그를 확인해줘.`
- `unknown-api 상태를 확인해줘.`

## 확인 대상

- Web Application 질문 입력
- 실행 결과 화면 표시
- 오류 화면 표시
- Tool Schema
- Tool 선택
- Tool Arguments
- Tool Result
- Structured Output
- Streaming Event
- Responses API Usage
- Tool 실행 시간
- 404 오류 전달
- FastAPI 연결 실패

## 범위 제외

- OpenAI Agents SDK
- Agent
- Agent Loop
- FastMCP
- MCP Client
- MCP Server
- Human Approval
- Handoff
- Multi-Agent
- Write Tool

## 완료 조건

기획서의 Phase 1 검증 항목을 실제 실행으로 확인한 경우에만 완료 처리.

OpenAI API 실행에 필요한 환경이 없어 검증하지 못한 경우 구현 완료와 Phase 완료를 구분해 보고.

실제 검증 완료 후에만 `docs/phase1-tool-calling.md` 작성.