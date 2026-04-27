# NotebookLM ↔ Gemini Bridge

Gemini 사이드패널 노트북 활성화 + 토론모드 컨텍스트 주입 절차.

## 배경
2026-04-08부터 Gemini 앱에 NotebookLM이 통합되어 사이드패널에서 노트북을 직접 호출할 수 있다.
한쪽에 추가한 소스가 다른 쪽에 자동 동기화되므로 Gemini 챗에서도 노트북 컨텍스트로 응답한다.

## A. Gemini 사이드패널로 노트북 활성화 (메인 흐름)

### Step 1. CDP Chrome 진입 확인
- 토론모드와 동일: 포트 9222 / 프로필 `C:\temp\chrome-cdp` 필수
- `90_공통기준/토론모드/CLAUDE.md` "CDP Chrome 단독 사용" 참조

### Step 2. Gemini 페이지 활성화
- `mcp__chrome-devtools-mcp__list_pages` → gemini.google.com 페이지 찾기
- 없으면 `new_page(url=<gemini_gem_url>)`
- `select_page(pageId, bringToFront=true)` 활성화

### Step 3. 사이드패널에서 노트북 선택
- 사이드패널 진입 후 대상 노트북(`gemini_label` 일치) 선택
- 노트북 활성화 시 입력창에 노트북 컨텍스트 인디케이터 표시됨
- **셀렉터 검증 필요** — Gemini UI는 변경이 잦음. 첫 1회 실행 시 take_snapshot으로 확인

### Step 4. 질의 전송
- 기존 `/gemini-send` 절차 그대로 사용
- 노트북이 활성화된 상태에서는 응답이 노트북 소스 기반

### Step 5. 응답 수령
- `/gemini-read`

> **주의**: Gemini UI 사이드패널 셀렉터는 롤아웃·UI 개편에 따라 변동 가능.
> 첫 사용 시 `take_snapshot` 실측 후 셀렉터 확정. 본 문서에 추가.

## B. NotebookLM MCP 직접 질의 → Gemini 컨텍스트 주입 (Fallback)

Gemini 사이드패널 통합이 미반영된 경우(롤아웃 미완 / 권한 미부여), MCP 응답을 Gemini 챗 컨텍스트로 주입한다.

### Step 1. NotebookLM MCP 질의
```
mcp__notebooklm-mcp__select_notebook(query="<도메인 또는 이름>")
mcp__notebooklm-mcp__ask_question(question="<질문>")
```

### Step 2. 응답 정규화 (Claude가 수행)
- 인용 marker 정리, 핵심 발췌 추출
- 토큰 절약을 위해 200~400자 요약본 생성

### Step 3. Gemini 챗에 주입
- `/gemini-send`로 다음 형식 전송:
```
[노트북 근거 — <노트북명>]
<NotebookLM 응답 발췌·인용>

[질문]
<원래 토론 주제 또는 후속 질문>
```

### Step 4. Gemini 응답 수령 후 토론 계속
- `/gemini-read`

## C. 토론모드(3-way)에서 노트북 근거 활용

> 라운드 시작 전 양측에 동일한 NotebookLM 근거 배포 → 검증 일관성 확보.

1. Round 시작 전 Claude가 `mcp__notebooklm-mcp__ask_question`으로 도메인 근거 수집
2. 발췌본을 `[근거]` 블록으로 라운드 페이로드 상단에 삽입
3. GPT·Gemini 양측에 동일 페이로드 전송 (gpt-send / gemini-send)
4. 응답 하네스 라벨링 시 `[근거]`와의 일치도 검증 (실증됨/일반론 라벨 판정에 사용)

## 셀렉터 메모 (실측 후 채움)

- 사이드패널 토글 버튼: _(미확정 — take_snapshot으로 확인)_
- 노트북 목록 컨테이너: _(미확정)_
- 노트북 항목 클릭 가능 셀렉터: _(미확정)_
- 활성 노트북 인디케이터: _(미확정)_

## 변경 이력
- 2026-04-27 신설 (사용자 지시 — Gemini 메인 / NotebookLM 데이터 레이어)
