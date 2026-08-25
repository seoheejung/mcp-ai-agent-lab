# index-result.html 작성 지시서

현재 프로젝트의 실제 구현 결과와 Phase 1~6 완료 문서를 기준으로, **MCP와 AI Agent 개념을 처음 보는 사람도 이해할 수 있는 설명형 HTML 페이지**를 작성한다.

결과 파일:

```text
docs/index-result.html
```

## 목적

이 문서는 프로젝트 기획서나 구현 상세 문서를 그대로 옮기는 문서가 아니다.

Claude의 ELI5 스타일처럼 복잡한 개념을 쉽게 풀어서,

* 이 Phase에서 무엇을 만들었는지
* 왜 이 작업이 필요한지
* 이전 Phase와 무엇이 달라졌는지
* 실제 실행 결과로 무엇을 확인했는지
* 다음 Phase로 넘어가면서 무엇이 추가되는지

를 한눈에 이해할 수 있게 설명한다.

백엔드 개발자가 MCP, Tool Calling, Agent, Human Approval, Multi-Agent의 관계를 **구현 흐름 중심으로 이해할 수 있는 페이지**를 목표로 한다.

---

## 작업 전 확인

다음 파일을 먼저 읽는다.

```text
AGENTS.md
.project/plan.md

docs/phase1-tool-calling.md
docs/phase2-agent-loop.md
docs/phase3-mcp-server.md
docs/phase4-agent-mcp.md
docs/phase5-human-approval.md
docs/phase6-multi-agent.md

docs/index.html
design.md
```

실제 구현 파일과 테스트도 필요한 범위에서 확인한다.

문서 내용과 실제 구현이 다르면 **실제 코드와 검증 결과를 우선 확인**하고, 확인되지 않은 내용을 작성하지 않는다.

---

## 핵심 작성 원칙

### 1. 쉽게 설명

전문 용어를 없애는 것이 아니라, 전문 용어를 먼저 보여준 뒤 쉽게 설명한다.

형식:

```text
Tool Calling
→ LLM이 필요할 때 개발자가 제공한 함수를 선택해서 호출하는 방식

Agent Loop
→ 한 번 호출하고 끝나는 것이 아니라
  결과를 보고 다시 판단하고 Tool을 추가 호출할 수 있는 실행 구조
```

과도한 비유는 사용하지 않는다.

정확성을 해치는 비유는 금지한다.

---

### 2. Phase 흐름 중심

Phase를 독립적인 기능 목록처럼 나열하지 않는다.

반드시 이전 Phase의 한계가 다음 Phase의 이유로 연결되게 작성한다.

전체 흐름:

```text
Phase 1
LLM이 Function Tool 호출
        ↓
Phase 2
LLM이 스스로 반복 판단하는 Agent Loop
        ↓
Phase 3
Tool을 MCP Server로 분리
        ↓
Phase 4
Agent가 MCP Tool 사용
        ↓
Phase 5
Write Tool 실행 전 Human Approval
        ↓
Phase 6
Agent 역할 분리 + Handoff
```

---

## 페이지 전체 구조

### Hero

다음 내용을 짧게 표현한다.

```text
MCP & AI Agent LAB

Tool Calling에서 Multi-Agent까지
직접 구현하고 실행해서 확인한 구조
```

보조 설명:

```text
하나의 Backend Diagnostics API를 기준으로
Function Tool → Agent Loop → MCP → Human Approval → Multi-Agent까지
단계별로 연결 구조를 확장한 실습 결과
```

---

## 전체 흐름 섹션

Phase 1~6 전체 변화를 한 화면에서 볼 수 있는 흐름을 제공한다.

예시 구조:

```text
사용자 요청
   ↓
LLM
   ↓
Function Tool
   ↓
Agent Loop
   ↓
MCP Server
   ↓
Agent + MCP
   ↓
Human Approval
   ↓
Multi-Agent
```

각 단계는 클릭하거나 스크롤하면 해당 Phase로 연결되게 구성한다.

---

# Phase 1. Tool Calling

## 이 작업은 무엇인가

LLM이 직접 Backend API를 호출하는 것이 아니라, 개발자가 정의한 Function Tool을 통해 Backend Diagnostics API를 사용할 수 있게 한 단계.

구조를 쉽게 보여준다.

```text
User
 ↓
LLM
 ↓
Function Tool
 ↓
Backend Diagnostics API
```

## 왜 했는가

LLM 자체는 프로젝트 내부 함수나 Backend API를 자동으로 실행하지 못한다.

외부 작업을 수행하려면 호출 가능한 Tool을 제공해야 한다.

Phase 1에서는 가장 기본적인 **LLM → Tool** 관계를 확인한다.

## 실제로 확인한 것

Phase 1 완료 문서에 기록된 실제 구현과 검증 결과만 사용한다.

Tool Discovery, Tool Call, Backend 응답, Structured Output 등 실제 확인한 내용을 요약한다.

## 핵심 한 줄

```text
LLM에게 "무엇을 할 수 있는지" Tool로 알려주면
LLM이 필요한 Tool을 선택해서 호출할 수 있다.
```

---

# Phase 2. Agent Loop

## 이 작업은 무엇인가

Phase 1의 단발성 Tool Calling을 반복 판단 구조로 확장한 단계.

구조:

```text
User
 ↓
Agent
 ↓
판단
 ↓
Tool 호출
 ↓
결과 확인
 ↓
다시 판단
 ↓
필요하면 다른 Tool 호출
 ↓
최종 답변
```

## 왜 했는가

Tool Calling은 Tool을 호출할 수 있게 만드는 기능이다.

Agent는 Tool 호출 결과를 보고 다음 행동을 다시 결정할 수 있다.

이 차이를 실제 실행으로 비교한다.

## 반드시 비교할 것

```text
Deterministic Workflow
vs
Diagnostics Agent
```

둘의 차이를 쉬운 표로 보여준다.

예:

| 구분      | Workflow | Agent      |
| ------- | -------- | ---------- |
| 실행 순서   | 개발자가 결정  | LLM이 판단    |
| Tool 선택 | 코드에 고정   | 실행 중 선택    |
| 반복 실행   | 코드로 정의   | Agent Loop |
| 예측 가능성  | 높음       | 상대적으로 낮음   |

실제 Tool Calls, LLM Requests, Token Usage, 실행 시간, Required Evidence는 Phase 2 실측값만 사용한다.

---

# Phase 3. MCP Server

## 이 작업은 무엇인가

Phase 1~2에서 애플리케이션 내부에 있던 Tool을 FastMCP Server로 분리한 단계.

구조:

```text
Before

Agent/Application
   ↓
Local Function


After

MCP Client
   ↓ stdio
FastMCP Server
   ↓
Backend Diagnostics API
```

## 왜 했는가

Tool을 특정 Agent 코드 내부 함수로만 두면 Tool과 Agent가 강하게 결합된다.

MCP를 사용하면 Tool 제공 영역을 별도 Server로 분리할 수 있다.

여기서는 MCP를 추상적으로 설명하지 말고, **실제로 Local Function이 stdio MCP Server로 분리된 변화**를 중심으로 설명한다.

## 실제 결과

실제 확인한 내용을 포함한다.

* FastMCP 3.4.7
* stdio
* Read-only Tool 3개
* 독립 MCP Client
* Discovery
* 정상 Tool 호출
* Schema
* 오류 전달
* `16 passed`
* `uv lock --check` 성공

실측 Tool 시간도 기록하되 성능 비교 결과처럼 표현하지 않는다.

---

# Phase 4. Agent + MCP

## 이 작업은 무엇인가

Phase 2의 Agent가 Local Function 대신 Phase 3의 MCP Tool을 사용할 수 있게 연결한 단계.

가장 중요한 비교 구조:

```text
같은 Diagnostics Agent

        ┌─ Local Function
Agent ──┤
        └─ MCPServerStdio → FastMCP
```

## 왜 했는가

Phase 3에서는 MCP Server 자체만 검증했다.

Phase 4에서는 실제 Agent가 MCP를 통해 Tool을 사용하는 구조까지 연결한다.

## 실제 결과

Local과 MCP를 나란히 비교한다.

| 항목                |          Local |            MCP |
| ----------------- | -------------: | -------------: |
| LLM Requests      |              2 |              2 |
| Input Tokens      |            871 |            819 |
| Output Tokens     |            385 |            375 |
| Total Tokens      |          1,256 |          1,194 |
| 실행 시간             | 13,315.2218 ms | 10,084.8971 ms |
| Required Evidence |              3 |              3 |

반드시 다음 설명을 포함한다.

```text
이 결과는 1회 실행값이다.

MCP가 Local Function보다 빠르다는 결론을 내리기 위한 실험이 아니다.

핵심 결과는 두 경로 모두 같은 Agent 목적 아래
필요한 Evidence를 확보하고 정상 실행됐다는 점이다.
```

오류 경로도 간단히 시각화한다.

```text
Local
→ LlmResponseError

MCP Agent
→ AgentRunError
   → LlmResponseError

직접 stdio
→ McpError
```

---

# Phase 5. Human Approval

## 이 작업은 무엇인가

처음으로 Write Tool을 추가하고, 실행 전에 사람의 승인을 요구한 단계.

구조:

```text
Agent
 ↓
restart_service 요청
 ↓
승인 필요
 ↓
Run 중단
 ├─ Approve
 │    ↓
 │  Tool 실행
 │
 └─ Reject
      ↓
    Tool 미실행
 ↓
같은 RunState 재개
```

## 왜 했는가

Read Tool과 달리 시스템 상태를 변경하는 Write Tool은 Agent가 판단했다는 이유만으로 즉시 실행하면 위험할 수 있다.

그래서 중요한 작업 앞에 사람의 승인 지점을 둔다.

## 강조할 핵심

```text
Human Approval은
"Agent가 판단하지 못하게 만드는 기능"이 아니다.

Agent가 실행하려는 중요한 작업을
실행 직전에 사람이 허용하거나 거절하는 제어 지점이다.
```

## 실제 결과

* `restart_service`만 승인 대상
* Read Tool은 기존 방식 유지
* Approve 실제 실행
* Reject 실제 미실행
* 동일 RunState 재개
* 실제 Docker/서버 재시작 없음
* fixture 상태만 변경
* `21 passed`

Usage:

| 실행      | Requests | Input | Output | Total |             시간 |
| ------- | -------: | ----: | -----: | ----: | -------------: |
| Approve |        3 | 1,543 |    281 | 1,824 | 17,021.1084 ms |
| Reject  |        3 | 1,545 |    378 | 1,923 | 17,586.8578 ms |

Pending RunState가 현재 프로세스 메모리에만 저장된다는 현재 구현 범위도 명시한다.

SDK 자체 한계처럼 표현하지 않는다.

---

# Phase 6. Multi-Agent

## 이 작업은 무엇인가

하나의 Agent가 모든 역할을 처리하던 구조를 두 역할로 분리하고 Handoff를 연결한 단계.

```text
Diagnostics Agent
        │
        │ Handoff
        ▼
Operations Agent
```

역할:

```text
Diagnostics Agent
→ 진단 담당
→ Read Tool만 사용

Operations Agent
→ 운영 작업 담당
→ status / restart Tool 사용
```

## 왜 했는가

Agent가 많으면 좋은 것이 아니다.

하나의 Agent에 모든 역할과 Tool을 몰아넣는 대신, 역할과 Tool 권한을 분리했을 때 실행 흐름이 어떻게 달라지는지 확인하기 위한 단계다.

## Handoff 쉽게 설명

```text
Diagnostics Agent가
"이제 이 작업은 Operations 역할이 처리해야 한다"고 판단하면

현재 작업의 담당 Agent를 Operations Agent로 넘긴다.
```

Manager나 Agents-as-Tools 방식과 섞지 않는다.

이번 프로젝트에서는 **Handoff 방식만 구현했다**고 명확히 표시한다.

## 실제 흐름

```text
User
 ↓
Diagnostics Agent
 ↓
Read Tool
 ↓
Operations 작업 필요
 ↓
Handoff
 ↓
Operations Agent
 ↓
restart_service
 ↓
Human Approval
 ├─ Approve
 └─ Reject
```

## 실제 비교 결과

| 실행                    | LLM Requests | Total Tokens |        전체 시간 |
| --------------------- | -----------: | -----------: | -----------: |
| Single Agent          |            2 |        1,518 | 13,017.47 ms |
| 명시적 Handoff + Approve |            4 |        2,428 | 19,531.75 ms |
| 자율 판단 + Reject        |            4 |        2,542 | 14,719.23 ms |

반드시 다음 내용을 같이 표시한다.

```text
Single Agent 실행에서는 restart approval이 발생하지 않았다.

따라서 세 실행은 완전히 동일한 실행 경로가 아니다.

이 측정값으로 Multi-Agent 자체의 성능 비용을 일반화하지 않는다.
```

---

# 마지막 정리 섹션

## 프로젝트에서 실제로 달라진 것

한눈에 비교할 수 있는 표를 만든다.

| Phase | 핵심 변화                | 제어 주체             |
| ----- | -------------------- | ----------------- |
| 1     | Function Tool 연결     | LLM               |
| 2     | 반복 Tool 판단           | Agent             |
| 3     | Tool을 MCP Server로 분리 | MCP Client/Server |
| 4     | Agent가 MCP Tool 사용   | Agent + MCP       |
| 5     | Write 실행 전 승인        | Human             |
| 6     | 역할별 Agent 분리         | Agent Handoff     |

---

## 개념 구분

최종적으로 아래 개념을 짧고 명확하게 구분한다.

### LLM

```text
입력을 보고 다음 출력을 생성하는 모델
```

### Tool Calling

```text
LLM이 외부 기능을 호출할 수 있게 하는 방식
```

### Workflow

```text
개발자가 실행 순서를 정한 구조
```

### Agent

```text
실행 중 다음 행동과 Tool 사용 여부를 LLM이 판단하는 구조
```

### MCP

```text
Agent 자체가 아니라
Tool과 AI 애플리케이션을 연결하기 위한 표준화된 프로토콜
```

### Human Approval

```text
중요한 Tool 실행 전에 사람이 허용 또는 거절하는 제어 지점
```

### Handoff

```text
현재 Agent가 다른 Agent에게 실행 주도권을 넘기는 방식
```

### Multi-Agent

```text
역할이 다른 여러 Agent가 하나의 작업 흐름에 참여하는 구조
```

---

## 반드시 포함할 핵심 메시지

페이지 마지막에는 다음 의미가 전달되어야 한다.

```text
MCP = Agent가 아니다.
Tool Calling = Agent가 아니다.
Multi-Agent = Agent를 많이 만드는 것이 목적이 아니다.

이 프로젝트에서는 하나의 Backend Diagnostics 환경을 유지하면서
실행 제어권과 Tool 연결 방식이 Phase마다 어떻게 달라지는지를
실제 코드와 실행 결과로 확인했다.
```

---

## 디자인 기준

기존 `docs/index.html`과 프로젝트 디자인 방향을 유지하되 그대로 복제하지 않는다.

`index-result.html`은 **설명과 결과 이해에 최적화된 페이지**로 구성한다.

### UI 구성

* 상단 고정 또는 스크롤 기반 Phase Navigation
* Phase별 독립 카드 또는 섹션
* 구조 변화는 HTML/CSS 기반 다이어그램 또는 Mermaid 사용
* Before / After 비교 적극 활용
* 실제 측정값은 표 또는 작은 Metric Card 사용
* 핵심 개념은 강조 박스 사용
* 성공/실패처럼 보이는 과도한 색상 사용 금지
* 숫자보다 구조와 의미가 먼저 보이게 구성
* 모바일에서도 읽을 수 있는 반응형 구성

### 접근성

* Semantic HTML 사용
* heading 단계 준수
* 버튼에 명확한 accessible name 제공
* 필요한 상태 영역에 `aria-live`
* 색상만으로 의미 전달 금지
* 키보드 탐색 가능
* 충분한 contrast 유지
* `prefers-reduced-motion` 고려

---

## 금지 사항

* 실제로 구현하지 않은 기능 추가 금지
* Phase 7 또는 이후 기능 추가 금지
* RAG, Memory, Manager Agent, Agents-as-Tools, 병렬 Agent 추가 금지
* MCP Resources/Prompts/Streamable HTTP를 구현한 것처럼 표현 금지
* 성능 실측값을 일반적인 성능 우열로 확대 해석 금지
* 공식 문서에 없는 동작을 SDK 기능으로 단정 금지
* Trace ID, API Key, 환경 변수 실제 값 노출 금지
* 프로젝트 결과를 성공 사례처럼 과장 금지
* 기존 `docs/index.html` 삭제 또는 대체 금지
* 기존 Phase 결과 문서 수정 금지
* `.project/plan.md` 수정 금지

---

## 완료 기준

* [ ] `docs/index-result.html` 생성
* [ ] Phase 1~6 모두 포함
* [ ] 각 Phase에 `무엇을 했는가 / 왜 했는가 / 실제 결과` 포함
* [ ] 이전 Phase → 현재 Phase 변화가 시각적으로 확인 가능
* [ ] 실제 검증값만 사용
* [ ] Phase 4~6 Usage 실측값 정확히 반영
* [ ] Single Agent 비교 조건 차이 명시
* [ ] MCP / Agent / Tool Calling / Workflow 개념 혼동 없음
* [ ] Human Approval과 Backend 인증·인가 혼동 없음
* [ ] Handoff와 Manager 패턴 혼동 없음
* [ ] 기존 프로젝트 디자인과 시각적 일관성 유지
* [ ] 반응형 및 기본 웹 접근성 확인
* [ ] HTML을 실제 브라우저에서 열어 렌더링 확인
* [ ] 기존 테스트에 영향 없는지 확인
* [ ] 검증하지 않은 내용을 문서에 추가하지 않음

작업 완료 후에는 변경 파일, 페이지 구성, 실제 확인한 렌더링·테스트 결과만 보고한다.
