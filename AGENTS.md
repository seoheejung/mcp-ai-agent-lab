# MCP & AI Agent LAB - Codex Instructions

> Codex가 이 저장소에서 작업할 때 항상 적용하는 공통 규칙

## 1. 기준 문서

작업 전 다음 순서로 확인한다.

1. `AGENTS.md`
2. `.project/plan.md`
3. 현재 Phase의 `docs/instructions/phaseN-*.md`
4. `design.md`
5. 현재 저장소의 실제 코드와 설정

기능·Phase 범위의 최종 기준은 `.project/plan.md`다.

현재 Phase의 세부 구현·검증 범위는 `docs/instructions/phaseN-*.md`를 따른다.

Web Application의 화면 설계와 웹 접근성은 `design.md`를 따른다.

문서가 충돌하면 다음 우선순위를 적용한다.

```text
사용자의 현재 명시적 지시
→ .project/plan.md
→ 현재 Phase 지침
→ design.md
→ AGENTS.md
```

`.project/plan.md`가 없거나 읽을 수 없는 경우 기획을 추측해서 구현하지 않는다.

---

## 2. 작업 범위

현재 요청된 Phase만 수행한다.

이후 Phase의 기능, API, Tool, Agent, 설정, 코드, 결과 파일을 선반영하지 않는다.

기존 구현을 먼저 확인한 뒤 현재 Phase에 필요한 최소 범위만 수정한다.

현재 작업과 관계없는 리팩터링, 추상화, 기능 추가 금지.

실제 저장소와 실행 결과를 기준으로 판단한다.

확인하지 않은 API, 실행 결과, 성능, Usage 값을 작성하지 않는다.

---

## 3. 구현 기준

Python `3.13.14`를 유지한다.

외부 패키지는 prerelease가 아닌 정식 배포 버전만 사용한다.

설치 전 Python 3.13.14 호환성과 공식 API를 확인한다.

실제 의존성 버전은 `pyproject.toml`과 `uv.lock`을 기준으로 한다.

비밀 값은 환경 변수로 관리한다.

금지:

- API Key 코드 작성
- API Key 로그 출력
- `.env` Git 포함
- Browser에 `OPENAI_API_KEY` 노출

Frontend는 기획서 기준의 HTML, CSS, JavaScript를 사용한다.

Browser에서 OpenAI API를 직접 호출하지 않는다.

FastAPI Endpoint와 AI Tool의 책임을 분리한다.

FastAPI Endpoint를 FastMCP Tool로 자동 변환하지 않는다.

---

## 4. 품질 및 검증

코드 작성만으로 완료 처리하지 않는다.

기본 흐름:

```text
구현
→ 실행
→ 테스트
→ 실제 결과 확인
→ 코드·보안·운영 안정성 검토
→ Regression Test
→ 문서화
```

검토 기준:

- 현재 Phase 목적 달성 여부
- 불필요한 코드·추상화·중복 여부
- 잠재적 버그와 예외 처리
- 비동기 I/O 및 Resource 정리
- 비밀 값 노출과 권한 경계
- 불필요한 네트워크·Tool 호출
- 현재 Phase 범위 이탈 여부

문제 발견 시:

```text
문제 확인
→ 원인 확인
→ 재현
→ 최소 수정
→ 관련 테스트
→ Regression 확인
```

현재 Phase 범위를 벗어나는 개선은 구현하지 않고 남은 문제로 보고한다.

Web Application을 수정한 경우 `design.md` 기준의 화면과 웹 접근성을 검증한다.

---

## 5. 코드 스타일

기존 프로젝트 스타일을 유지한다.

Python 주석은 필요한 경우에만 작성한다.

주석은 짧고 직접적인 명사형 표현을 사용한다.

예:

```python
# 환경 변수 값 조회
# Backend 응답 검증
# MCP Tool 결과 변환
# Approval 상태 확인
```

사용하지 않는 코드, Import, Debug 코드는 제거한다.

현재 Phase와 관계없는 전체 파일 재포맷 금지.

---

## 6. Phase 문서

`docs/phaseN-*.md`는 현재 Phase 구현과 실제 실행 검증이 완료된 후에만 작성한다.

최상위 구조:

```text
# Phase N. 제목

## 학습 목표

## 실습

## 확인 결과
```

확인하지 않은 결과나 예상값을 작성하지 않는다.

실제 실행에서 확인한 내용만 기록한다.

---

## 7. Git 작업

작업 시작 전 `git status`를 확인한다.

현재 작업과 관계없는 기존 변경 파일을 수정하거나 제거하지 않는다.

금지:

- Reset
- Rebase
- Force Push
- Phase 완료 전 임시 Commit
- 검증 실패 상태의 완료 Commit

현재 Phase 구현·검증·문서화와 필수 테스트가 완료된 경우 Commit한다.

Commit Message:

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

Commit 이후 `git status`를 확인한다.

`git push`는 실행하지 않는다.

---

## 8. 완료 보고

작업 완료 시 다음만 보고한다.

1. 구현 내용
2. 생성·수정·삭제 파일
3. 테스트·검증 결과
4. 품질·보안·운영 안정성 검토 결과
5. Usage·측정 결과
6. 웹 접근성 검토 결과
7. 현재 Phase 범위 준수 여부
8. 미검증 또는 남은 문제
9. Commit Message 및 Commit Hash
10. Push 미실행 확인

성공하지 않은 항목을 성공으로 표현하지 않는다.

측정하지 않은 값을 추정해서 작성하지 않는다.
