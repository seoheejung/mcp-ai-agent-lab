# Phase 3. MCP Server 작업 지침

## 목적

Agent와 분리된 MCP 자체의 역할 검증.

FastAPI Backend 기능을 FastMCP Tool로 제공하고 MCP Client에서 직접 발견·호출한다.

LLM과 Agent 사용 금지.

## 선행 조건

Phase 1 Backend 기능 유지.

Phase 2 Agent 구현과 독립적으로 작업.

## 구현 범위

- FastMCP 정식 배포 버전 도입
- Web Application MCP 검증 화면 연결
- FastMCP Server
- MCP Tool 3개
- stdio Transport
- FastMCP 검증 Client
- Tool Discovery
- Input Schema
- Output Schema
- Structured Result
- MCP 오류 전달
- Tool 실행 시간 측정

## MCP Tool

- `get_service_status`
- `get_recent_metrics`
- `get_recent_logs`

각 Tool은 HTTPX를 통해 기존 FastAPI Backend 호출.

## FastMCP Test Client

목적:

- MCP 연결
- Tool Discovery
- Schema 확인
- 직접 Tool Call
- Error 확인

Phase 4 Agent 구현에서는 이 Test Client를 재사용하지 않는다.

## 검증 항목

- Server 실행
- stdio 연결
- `list_tools`
- 세 Tool Discovery
- Input Schema
- Output Schema
- Structured Result
- 정상 Tool Call
- 잘못된 Argument
- `unknown-api`
- FastAPI 미실행
- MCP Server 연결 실패

## 측정

- Tool Calls
- Tool Latency
- End-to-End Time
- Error Type

LLM Token 관련 값 생성 금지.

## 범위 제외

- Agent + MCP
- MCP Resources
- MCP Prompts
- Streamable HTTP
- Remote MCP
- Sampling
- Elicitation
- Human Approval
- Write Tool
- Handoff
- Multi-Agent

## 완료 조건

Agent 또는 LLM 없이 MCP Server의 Discovery와 Tool Call을 실제 확인한 경우에만 완료.

완료 후 `docs/phase3-mcp-server.md` 작성.