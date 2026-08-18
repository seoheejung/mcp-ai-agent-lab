# MCP & AI Agent Concepts

> MCP, Tool Calling, Workflow, AI Agent의 차이와 연결 구조를 백엔드 개발 관점에서 정리한 학습 문서

## 개요

MCP와 AI Agent를 처음 학습하면서 혼동하기 쉬운 개념을 분리하고, 각 기술이 어떤 역할을 담당하는지 구조적으로 이해하기 위한 프로젝트입니다.

단순 용어 정리가 아니라 LLM에서 Tool Calling, Agent Loop, MCP로 확장되는 흐름을 기준으로 정리합니다.

## 핵심 개념

| 개념           | 역할                                |
| ------------ | --------------------------------- |
| LLM          | 입력을 받아 추론하고 출력 생성                 |
| Chatbot      | LLM과 사용자가 대화할 수 있는 애플리케이션         |
| Tool Calling | LLM이 외부 함수 또는 기능 호출               |
| Workflow     | 개발자가 정의한 순서대로 LLM과 Tool 실행        |
| AI Agent     | LLM이 상황에 따라 다음 행동과 Tool 선택        |
| MCP          | AI 애플리케이션과 외부 Tool·Data 연결 방식 표준화 |
| MCP Server   | MCP 규격으로 Tool·Resource 등을 외부에 제공  |

## 핵심 구분

```text
Agent
=
무엇을 할 것인가 결정


Tool
=
실제 행동 수행


MCP
=
AI와 외부 Tool·Data 사이의 연결 방법 표준화
```

MCP와 AI Agent는 같은 기술이 아닙니다.

AI Agent가 외부 시스템을 사용하기 위한 방법 중 하나로 MCP를 사용할 수 있습니다.

## 전체 구조

```text
                 ┌───────────────┐
                 │     User      │
                 └───────┬───────┘
                         │ Goal
                         ▼
                 ┌───────────────┐
                 │   AI Agent    │
                 │               │
                 │ LLM + Loop    │
                 │               │
                 │ 무엇을 할지   │
                 │     판단      │
                 └───────┬───────┘
                         │
                        MCP
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ DB MCP  │   │Git MCP  │   │Docker   │
      │ Server  │   │ Server  │   │MCP      │
      └────┬────┘   └────┬────┘   └────┬────┘
           │             │             │
           ▼             ▼             ▼
      PostgreSQL       GitHub        Docker
```

## 학습 문서

[학습 문서 보기](https://seoheejung.github.io/mcp-ai-agent-concepts/)

다음 내용을 하나의 HTML 문서로 정리합니다.

* LLM과 Tool Calling
* Tool Calling과 AI Agent의 차이
* Agent Loop
* MCP의 역할
* MCP Client·Server 구조
* MCP Tools·Resources·Prompts
* MCP Server와 AI Agent의 역할 분리
* REST API 관점에서의 MCP 이해
* Workflow와 Agent 비교
* Multi-Agent와 단일 Agent 구분
* 직접 Function Calling과 MCP Tool 비교
* MCP와 AI Agent 학습 순서

## 학습 순서

```text
LLM
 ↓
Function / Tool Calling
 ↓
Agent Loop
 ↓
MCP
 ↓
Agent + MCP
 ↓
Guardrail / Human Approval
 ↓
Multi-Agent
```

처음부터 MCP, Multi-Agent, RAG를 함께 구성하지 않고 각 개념의 역할을 분리해서 이해하는 것을 기준으로 합니다.

## 참고 자료

* [Model Context Protocol — Introduction](https://modelcontextprotocol.io/docs/getting-started/intro)
* [Model Context Protocol — Architecture](https://modelcontextprotocol.io/docs/learn/architecture)
* [OpenAI Agents SDK — Running agents](https://openai.github.io/openai-agents-js/guides/running-agents/)
* [OpenAI Agents SDK — Handoffs](https://openai.github.io/openai-agents-python/handoffs/)
* [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
