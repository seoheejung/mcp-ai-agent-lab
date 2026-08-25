# Phase 4. Agent + MCP 작업 지침

## 목적

Phase 2 Diagnostics Agent와 Phase 3 FastMCP Server 결합.

Local Function Tool과 MCP Tool 연결 구조 비교.

## 선행 조건

- Phase 2 Agent 검증 완료
- Phase 3 MCP Server 검증 완료
- Backend와 Fixture 유지

## 구현 범위

- OpenAI Agents SDK의 MCP 연결 사용
- Web Application Agent + MCP 실행 화면 연결
- `MCPServerStdio`
- Diagnostics Agent의 MCP Tool 사용
- MCP Tool Discovery
- Agent Loop
- Structured Output
- Usage
- Tracing
- Local Function vs MCP 비교
- 오류 전파 비교

## 고정 조건

동일 유지:

- Backend
- Fixture
- 질문
- 모델
- Agent Instruction
- Output Schema
- Tool 의미

변경 변수:

`Local Function → MCP`

## 평가 질문

`order-api의 응답이 느려졌어. 원인을 조사해줘.`

## 비교 지표

- Success
- Tool Calls
- LLM Requests
- Input Tokens
- Output Tokens
- Total Tokens
- End-to-End Time
- Tool Time
- Required Evidence
- Error Path

MCP가 더 빠르거나 저렴하다는 사전 가정 금지.

## 오류 검증

- MCP Server 미실행
- FastAPI 미실행
- MCP Tool Error
- Agent의 MCP 오류 처리

## 범위 제외

- `restart_service`
- Human Approval
- Handoff
- Multi-Agent
- Streamable HTTP
- Remote MCP
- OAuth

## 완료 조건

같은 Agent 기능을 Local Function과 MCP 두 구조로 실제 실행·비교한 경우에만 완료.

완료 후 `docs/phase4-agent-mcp.md` 작성.

