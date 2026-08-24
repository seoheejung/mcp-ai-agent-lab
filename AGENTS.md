# MCP & AI Agent LAB - Codex Instructions

> Codex가 이 저장소에서 구현, 테스트, 검증, 품질 검토, 문서화 및 Git 작업을 수행할 때 적용하는 공통 규칙

## 1. 기준 문서

모든 작업은 로컬 전용 기획서 `.project/plan.md`를 최상위 프로젝트 기준으로 수행한다.

`.project/plan.md`는 Git에 포함하지 않는다.

`.gitignore`에 다음 경로를 유지한다.

```text
.project/
```

현재 Phase 작업 전 반드시 다음 순서로 확인한다.

1. `AGENTS.md`
2. `.project/plan.md`
3. 현재 Phase의 `docs/instructions/phaseN-*.md`
4. 현재 저장소의 실제 코드와 설정
5. 필요 시 `README.md`

`README.md`는 프로젝트 소개 문서이며 구현 범위의 최종 기준이 아니다.

현재 Phase 지침과 `.project/plan.md`가 충돌하면 `.project/plan.md`를 우선한다.

사용자가 기획 변경을 명시적으로 요청하지 않은 경우 `.project/plan.md`의 범위를 확대하거나 변경하지 않는다.

`.project/plan.md`가 존재하지 않거나 읽을 수 없는 경우 기획 내용을 추측해서 구현하지 않는다.

기획서 확인 불가 상태를 사용자에게 보고하고 구현 작업을 진행하지 않는다.

---

## 2. Phase 범위

현재 요청된 Phase만 수행한다.

이후 Phase의 기능, 패키지, 클래스, 설정, API, 문서, 결과 파일을 선반영하지 않는다.

금지 기준:

* Phase 1에서 Agent 구현 금지
* Phase 2에서 MCP 구현 금지
* Phase 3에서 Agent + MCP 연결 금지
* Phase 4에서 Write Tool 및 Human Approval 구현 금지
* Phase 5에서 Multi-Agent 구현 금지
* Phase 6에서 계획에 없는 Agent 추가 금지

한 번에 하나의 핵심 변경 요소만 추가한다.

현재 Phase를 위해 필요하지 않은 미래 확장 포인트 추가 금지.

---

## 3. 기술 기준

Python 버전:

```text
3.13.14
```

Python 버전을 임의로 변경하지 않는다.

패키지는 prerelease가 아닌 정식 배포 버전만 사용한다.

사용 금지:

* alpha
* beta prerelease
* rc
* dev
* preview

외부 패키지 설치 전 확인:

* Python 3.13.14 호환 여부
* 정식 배포 여부
* 공식 문서의 현재 API
* 기존 의존성과 충돌 여부
* 알려진 중대한 호환 문제 여부

실제 설치 버전은 `pyproject.toml`과 `uv.lock`을 기준으로 한다.

Phase 진행 중 근거 없는 의존성 업그레이드 금지.

---

## 4. 공통 기술

기획서 범위 내 기술:

* Python 3.13.14
* FastAPI
* Uvicorn
* HTTPX
* Pydantic
* OpenAI Responses API
* OpenAI Agents SDK Python
* FastMCP
* pytest
* pytest-asyncio
* uv

현재 Phase에서 필요하지 않은 기술은 설치하지 않는다.

---

## 5. 환경 설정

비밀 값과 환경별 값은 환경 변수 기반으로 관리한다.

주요 변수:

* `OPENAI_API_KEY`
* `OPENAI_MODEL`
* `BACKEND_BASE_URL`

금지:

* 비밀 값 코드 직접 작성
* `.env` Git 포함
* API Key 로그 출력
* `.env.example` 실제 비밀 값 작성

---

## 6. 구현 원칙

실제 저장소 파일과 실행 결과를 기준으로 판단한다.

추정으로 파일, API, Package API, 실행 결과를 작성하지 않는다.

기존 구현을 먼저 확인한 뒤 최소 범위로 수정한다.

현재 Phase와 직접 관련 없는 리팩터링 금지.

불필요한 추상화 금지.

향후 Phase를 위한 사전 구조 설계 금지.

현재 사용하지 않는 인터페이스나 확장 포인트 추가 금지.

FastAPI Endpoint와 AI Tool의 책임을 분리한다.

FastAPI 전체 Endpoint를 FastMCP Tool로 자동 변환하지 않는다.

MCP Tool은 기획서의 AI 사용 목적에 맞게 명시적으로 정의한다.

코드를 추가하기 전에 기존 코드로 목적 달성이 가능한지 먼저 확인한다.

새 코드보다 기존 코드의 단순한 수정으로 해결 가능한 경우 최소 변경을 우선한다.

---

## 7. 설계 및 코드 품질 검토

구현 완료 직후 바로 완료 처리하지 않는다.

현재 Phase 범위 안에서 전체 변경 사항을 다시 검토한다.

다음 질문을 기준으로 검토한다.

### 설계

* 책임과 경계가 명확한가?
* 현재 문제에 비해 구조가 과도하게 복잡하지 않은가?
* 의존 방향이 자연스러운가?
* 현재 Phase 목적과 직접 연결되는 설계인가?
* 미래 기능을 예상한 과도한 추상화가 없는가?
* 더 단순한 구조로 같은 목적을 달성할 수 없는가?

설계의 우아함은 클래스 수나 패턴 수가 아니라 책임 분리, 단순한 의존 관계, 변경 범위의 명확성을 기준으로 판단한다.

### 코드 간결성

* 불필요하게 긴 코드가 없는가?
* 불필요한 Wrapper가 없는가?
* 단순한 로직을 과도하게 분리하지 않았는가?
* 읽기 어려운 중첩이나 분기가 없는가?
* 불필요한 설정이나 상수가 없는가?

### 잠재적 버그

* `None` 또는 빈 값 처리 누락
* 예외 누락
* 잘못된 상태 전이
* 비동기 처리 누락
* Resource 정리 누락
* 공유 상태 오염
* 테스트 간 Fixture 상태 누출
* 잘못된 Timeout 처리
* 오류를 정상 결과처럼 반환하는 코드

### 목적 달성

* 기획서의 현재 Phase 목표를 실제로 달성했는가?
* 핵심 실행 경로가 실제로 동작하는가?
* 구현만 존재하고 사용되지 않는 코드가 없는가?
* 검증 항목이 실제 실행 결과로 확인됐는가?

### 보안

* 비밀 값 노출 가능성이 없는가?
* 외부 입력 검증이 충분한가?
* Read·Write 권한 경계가 유지되는가?
* Tool에 필요 이상의 권한이 없는가?
* 외부 입력이 Shell Command 등 위험한 실행 경로로 직접 전달되지 않는가?
* 로그에 민감 정보가 남지 않는가?

### 중복

* 동일 로직의 실제 중복이 존재하는가?
* 공통 함수 또는 모델로 합쳤을 때 책임이 더 명확해지는가?
* 단순히 비슷해 보인다는 이유로 성급하게 공통화하지 않았는가?

공통화는 실제 중복이 확인되고 복잡도를 줄이는 경우에만 수행한다.

미래 중복을 예상한 추상화 금지.

### 성능

* 불필요한 네트워크 호출이 없는가?
* 동일 Tool 또는 API를 불필요하게 반복 호출하지 않는가?
* 비동기 I/O를 Blocking 방식으로 처리하지 않는가?
* Client 또는 연결 객체를 비효율적으로 생성·폐기하지 않는가?
* 불필요한 데이터 변환이나 복사가 없는가?

측정 근거가 없는 성능 최적화 금지.

성능 문제를 발견한 경우 실제 측정 후 수정한다.

### 불필요한 코드

* 호출되지 않는 함수
* 사용되지 않는 Import
* 사용되지 않는 모델
* 죽은 분기
* 임시 Debug 코드
* 중복 설정
* 현재 Phase에서 필요하지 않은 코드
* 삭제해도 현재 동작에 영향이 없는 코드

삭제 가능한 코드는 테스트로 영향 범위를 확인한 뒤 제거한다.

---

## 8. 운영 안정성 및 지속가능성 검토

현재 Phase 구현 완료 후 운영 안정성과 유지보수성을 저해할 수 있는 요소를 확인한다.

주요 검토 대상:

* 예외 누락
* Timeout 부재
* 무한 또는 과도한 Retry
* Resource 정리 누락
* Client lifecycle 문제
* 비동기 Task 누수
* Fixture 상태 오염
* 실행 간 상태 누출
* 오류 원인 손실
* 로그 부족 또는 과도한 로그
* 비밀 정보 노출
* 불필요한 결합
* 변경 영향 범위 과대
* 테스트하기 어려운 구조
* 외부 서비스 장애 시 복구 불가능한 구조
* 실패가 다른 계층으로 연쇄 전파되는 구조

발견한 문제를 한 번에 대규모 리팩터링하지 않는다.

다음 순서로 고도화한다.

```text
문제 식별
→ 원인 확인
→ 재현 테스트 작성 또는 기존 테스트로 재현
→ 최소 수정
→ 해당 테스트 재실행
→ 관련 테스트 실행
→ 전체 Regression 확인
```

현재 Phase 범위를 벗어나는 개선은 구현하지 않고 별도 리스크로 보고한다.

---

## 9. 단계별 테스트 및 고도화

변경 후 한 번에 전체 테스트만 실행하고 끝내지 않는다.

가능한 범위에서 다음 순서로 진행한다.

### 1단계. 구조 및 정적 확인

* Import 오류
* Type 오류
* 설정 오류
* 사용되지 않는 코드
* 명백한 보안 문제
* Phase 범위 이탈

### 2단계. Unit Test

대상:

* Pydantic Model
* Fixture
* Backend Service
* Tool Argument Validation
* Error Mapping

### 3단계. API Test

해당 Phase에 FastAPI 변경이 있는 경우:

* Endpoint
* HTTP Status
* Response Schema
* Validation
* 상태 변경

### 4단계. MCP Integration Test

MCP가 현재 Phase 범위인 경우:

* stdio 연결
* Tool Discovery
* Tool Call
* Structured Result
* MCP Error

### 5단계. Agent Integration Test

Agent가 현재 Phase 범위인 경우:

* Tool Selection
* Agent Loop
* Structured Output
* Approval
* Handoff

현재 Phase에 존재하지 않는 기술의 테스트를 억지로 추가하지 않는다.

각 단계 실패 시 다음 단계로 넘어가기 전에 원인을 확인한다.

수정 후 실패한 단계부터 다시 실행하고 관련 Regression Test까지 확인한다.

---

## 10. 비동기 처리

네트워크 I/O는 기획서 기준에 따라 비동기 방식 사용.

주요 대상:

* FastAPI async Endpoint
* HTTPX AsyncClient
* FastMCP async Tool
* OpenAI async API
* Agents SDK async Runner

이유 없는 sync/async 혼합 금지.

Coroutine 미호출, await 누락, Client 종료 누락 여부 확인.

---

## 11. Structured Data

문자열 파싱보다 명시적인 Schema 사용.

기준:

* FastAPI: Pydantic
* Function Tool: Type Hint / JSON Schema
* Agent Output: Pydantic `output_type`
* MCP Tool: 명시적 Type Annotation / Pydantic

실제 Schema를 검증하지 않은 경우 완료 처리하지 않는다.

---

## 12. 오류 처리

오류를 정상 결과로 숨기지 않는다.

구분 대상:

* FastAPI Validation Error
* Service Not Found
* HTTP Client Error
* Backend Connection Error
* Backend Timeout
* Function Tool Error
* MCP Connection Error
* MCP Tool Error
* LLM API Error
* Agent Run Error
* Approval Rejection
* Handoff Error

Retry는 일시적 오류에만 적용한다.

Retry 비대상:

* Validation Error
* 404 Service Not Found
* 잘못된 Tool Argument
* Approval Reject

무한 Retry 금지.

SDK 기본 Retry가 존재하는 경우 먼저 확인하고 중복 Retry를 추가하지 않는다.

---

## 13. 테스트 및 검증

코드 작성만으로 완료 처리하지 않는다.

기본 흐름:

```text
구현
→ 실행
→ 단계별 테스트
→ 실제 결과 확인
→ 품질 검토
→ Regression Test
→ 문서화
```

실행하지 못한 검증은 명확하게 미검증으로 보고한다.

테스트를 통과시키기 위해 기대 결과를 실제 구현에 맞춰 임의 수정하지 않는다.

구현이 기획서와 다르면 구현을 수정한다.

---

## 14. 평가

비교 실험에서는 가능한 한 동일 조건 유지:

* 같은 Backend
* 같은 Fixture
* 같은 질문
* 같은 모델
* 같은 Prompt
* 같은 Tool 의미

자연어 문장의 완전 일치를 성공 기준으로 사용하지 않는다.

평가 대상:

* Tool 선택
* Required Evidence
* Forbidden Tool
* Structured Output
* Error Type
* Approval
* Handoff

측정되지 않은 숫자를 생성하지 않는다.

기대한 결론에 맞게 결과를 해석하거나 수정하지 않는다.

---

## 15. Usage 및 Tracing

실제 SDK 또는 실행 결과에서 제공되는 값만 기록한다.

가능한 측정값:

* LLM Requests
* Input Tokens
* Output Tokens
* Total Tokens
* Tool Calls
* Tool Latency
* End-to-End Time

Agent Phase에서는 실제 Trace를 확인한다.

모델의 비공개 Chain-of-Thought 저장 및 출력 금지.

Trace에 민감 정보가 포함되지 않는지 확인한다.

---

## 16. 웹 접근성

웹사이트, 웹페이지, 웹앱 또는 HTML UI를 생성·수정하는 작업에서는 웹 접근성을 필수 검증 항목으로 포함한다.

`docs/index.html` 수정도 해당 기준 적용 대상이다.

반드시 전체 검수한다.

### 키보드 접근성

마우스 없이 키보드만으로 모든 주요 기능을 사용할 수 있어야 한다.

확인:

* Tab 및 Shift+Tab 이동 가능
* 논리적인 Focus 이동 순서
* DOM 구조와 시각적 흐름의 일치
* 버튼, 링크, Form Control의 키보드 활성화
* Keyboard Trap 없음
* 숨겨진 요소로 Focus 이동 없음
* Modal 또는 Overlay 사용 시 올바른 Focus 처리

단순히 요소를 화면에 나열하지 않는다.

사용 흐름을 기준으로 논리적인 문서 구조와 Focus 순서를 구성한다.

### Focus 표시

현재 Focus 위치를 시각적으로 확인할 수 있어야 한다.

브라우저 기본 Focus 스타일을 이유 없이 제거하지 않는다.

Custom Focus 스타일 사용 시 충분히 명확한 강조 표시 제공.

`:focus-visible` 사용 가능 여부 검토.

### 스크린리더

의미에 맞는 Semantic HTML 사용.

가능한 경우:

* `header`
* `nav`
* `main`
* `section`
* `article`
* `footer`
* `button`
* `a`
* `label`

등의 Native Element 우선 사용.

`div` 또는 `span`을 임의의 Button처럼 사용하지 않는다.

### 이미지 대체 텍스트

정보 전달 이미지:

* 의미 있는 `alt` 제공

장식 이미지:

```html
alt=""
```

사용

파일명이나 의미 없는 문구를 `alt`로 사용하지 않는다.

### Form

Form Control에 연결된 Label 제공.

Placeholder만으로 Label 역할을 대체하지 않는다.

오류 상태와 오류 내용을 시각적으로만 전달하지 않는다.

### Heading 구조

Heading Level을 디자인 크기 목적으로 사용하지 않는다.

문서 구조에 맞는 순차적 Heading 구성.

### ARIA

Native HTML로 해결 가능한 경우 ARIA보다 Native Element 우선.

불필요한 ARIA 추가 금지.

ARIA 사용 시 Role, Name, State가 실제 UI 상태와 일치하는지 확인한다.

### 추가 확인

* Link 목적의 명확성
* 색상만을 이용한 상태 전달 금지
* 텍스트 확대 시 주요 정보 손실 여부
* 주요 콘텐츠의 읽기 순서
* 반복 Navigation 존재 시 Skip Navigation 필요성
* 동적 상태 변경의 Screen Reader 전달 필요성

자동 접근성 검사 도구를 사용할 수 있는 경우 보조 수단으로 사용한다.

자동 검사만으로 접근성 검증 완료 처리하지 않는다.

키보드 조작과 문서 구조를 직접 확인한다.

웹 UI를 생성·수정하지 않은 Phase에서는 완료 보고에 `웹 접근성: 해당 없음`으로 명시한다.

---

## 17. 코드 스타일

Python의 기존 코드 스타일을 유지한다.

필요한 경우에만 주석 작성.

주석은 짧고 직접적인 명사형 표현 사용.

예:

* 환경 변수 값 조회
* Backend 응답 검증
* MCP Tool 결과 변환
* Approval 상태 확인

불필요한 설명형 주석 금지.

---

## 18. Phase 문서

`docs/phaseN-*.md`는 해당 Phase 구현과 실제 실행 검증 완료 후에만 작성한다.

최상위 구조:

```text
# Phase N. 제목

## 학습 목표

## 실습

## 확인 결과
```

최상위 섹션 추가 금지.

확인하지 않은 결과 작성 금지.

예상값 작성 금지.

이후 Phase 기능 선반영 금지.

실제 Tool, Arguments, Result, Usage, Trace, Approval, Handoff, 실행 시간, 오류 등 실제 확인 결과만 기록한다.

---

## 19. Git 작업

작업 시작 전 Git 상태를 확인한다.

현재 작업과 관계없는 기존 변경 파일을 수정하거나 제거하지 않는다.

사용자가 요청하지 않은 Reset, Rebase, Force Push 금지.

현재 Phase 구현·검증·문서화가 완료되고 필수 테스트가 통과한 경우 Codex가 Commit까지 수행한다.

Commit Message 형식:

```text
feat: phase<단계>-<주요내용>
```

예:

```text
feat: phase1-tool-calling
feat: phase2-agent-loop
feat: phase3-mcp-server
feat: phase4-agent-mcp
feat: phase5-human-approval
feat: phase6-multi-agent
```

현재 Phase 완료 전 임시 Commit 금지.

검증 실패 또는 미해결 Blocking Issue가 있는 상태에서는 Phase 완료 Commit 금지.

Commit 이후 `git status`로 작업 트리 상태 확인.

Codex는 `git push`를 실행하지 않는다.

Push는 사용자가 Commit 내용과 검증 결과를 확인한 이후 직접 수행한다.

완료 보고에 다음 정보 포함:

* Commit Message
* Commit Hash
* Push 미실행 확인

---

## 20. 작업 완료 보고

작업 완료 시 다음 순서로 보고한다.

1. 구현 내용
2. 생성·수정·삭제 파일
3. 설계 및 코드 품질 검토 결과
4. 잠재적 버그 검토 결과
5. 보안 검토 결과
6. 중복·공통화·불필요 코드 검토 결과
7. 성능 및 운영 안정성 검토 결과
8. 실행 명령
9. 단계별 테스트·검증 결과
10. Usage 및 측정 결과
11. 웹 접근성 검토 결과 또는 해당 없음
12. 현재 Phase 범위 준수 여부
13. 미검증 또는 남은 문제
14. Git Commit Message 및 Commit Hash
15. Push 미실행 확인

성공하지 않은 항목을 성공으로 표현하지 않는다.

측정하지 않은 값을 추정해서 작성하지 않는다.

검토에서 발견한 문제가 현재 Phase 범위를 벗어나는 경우 임의 구현하지 않고 남은 리스크로 보고한다.
