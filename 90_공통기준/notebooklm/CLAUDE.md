# NotebookLM 컨트롤 레이어

> **목적**: NotebookLM ↔ Gemini 통합(2026-04-08~)을 우리 환경에서 일관되게 사용하기 위한 로컬 컨트롤 레이어.
> **메인 채널**: Gemini 웹 UI (사이드패널의 노트북 기능)
> **백엔드**: NotebookLM MCP (`mcp__notebooklm-mcp__*`) — 인증 확인·MCP 직접 질의·라이브러리 동기화용
> **단일 원본**: `registry.yaml` — 노트북 추가는 이 파일만 수정

## 진입점

| 트리거 | 경로 | 설명 |
|--------|------|------|
| `/notebooklm` | 슬래시 커맨드 | list/health/query/ask/sync/register 서브명령 |
| 도메인 키워드 (라인배치·정산) | 도메인 에이전트 | `line-batch-domain-expert`, `settlement-domain-expert` 자동 라우팅 |
| Gemini 토론 중 근거 필요 | bridge.md 절차 | NotebookLM 응답을 Gemini 컨텍스트로 주입 |

## 구조

```
90_공통기준/notebooklm/
├─ CLAUDE.md          ← 본 문서 (도메인 진입)
├─ registry.yaml      ← 노트북 목록·메타 (단일 원본)
├─ health.sh          ← MCP 인증·세션 점검
├─ sync.sh            ← registry ↔ MCP 라이브러리 차이 보고 (read-only)
├─ bridge.md          ← Gemini 사이드패널 통합 절차
└─ logs/              ← 질의 로그 (선택, .gitignore)
```

## 메인 사용 흐름 (Gemini-First)

### A. Gemini 사이드패널로 노트북 활성화 후 질의 (기본)
1. `/notebooklm ask <도메인> <질문>` 호출
2. 스킬 내부에서 `/gemini-send` 진입 + 사이드패널에서 해당 노트북 활성화
3. Gemini가 노트북 소스 + 일반 추론 결합한 답변 생성
4. `/gemini-read`로 응답 수령

### B. NotebookLM MCP 직접 질의 (소스 근거 인용 필요 시)
1. `/notebooklm query <도메인> <질문>` 호출
2. `mcp__notebooklm-mcp__select_notebook` → `mcp__notebooklm-mcp__ask_question`
3. 응답에 인용 marker 포함됨 (소스 근거)

### C. 도메인 에이전트 경유 (도메인 한정 질의)
- 라인배치 질의: `Agent(subagent_type="line-batch-domain-expert", ...)`
- 정산 질의: `Agent(subagent_type="settlement-domain-expert", ...)`
- 둘 다 내부적으로 `mcp__notebooklm-mcp__ask_question` 호출

## 확장 (노트북 추가)

1. NotebookLM 웹에서 새 노트북 생성 + 소스 업로드
2. `mcp__notebooklm-mcp__add_notebook` 또는 NotebookLM MCP 설정 파일에 등록
3. `registry.yaml`에 항목 추가 (name·url·domain·topics)
4. `/notebooklm sync` 실행 → registry ↔ MCP 일치 여부 확인
5. (선택) 새 도메인 에이전트 생성 — 기존 `line-batch-domain-expert` 패턴 복사

## 인증·운영

- 첫 사용 또는 MCP `authenticated=false`일 때 → `mcp__notebooklm-mcp__setup_auth` 1회 수행
- 세션 timeout: 기본 900초 — `list_sessions`로 잔여 시간 확인
- 인증 꼬임 시: `cleanup_data(confirm=true, preserve_library=true)` → `setup_auth` 재수행
- `health.sh` 실행 시 위 상태를 한 번에 보고

## 원칙

- [MUST] 노트북 추가는 `registry.yaml` 수정으로만. MCP 직접 추가만 하고 registry 누락 시 `sync.sh`가 차이 보고
- [MUST] 도메인 한정 질의는 도메인 에이전트 경유 — 메인 컨텍스트 보호
- [SHOULD] Gemini 사이드패널 = 메인 채널. MCP 직접 호출은 fallback 또는 인용 근거 명시 필요 시
- [NEVER] NotebookLM API 직접 호출 금지 (공식 API 미공개) — MCP 또는 웹 UI 경로만
- [NEVER] 노트북 URL 하드코딩 금지 — 항상 `registry.yaml`에서 조회

## 관련 문서

- 슬래시 커맨드: `.claude/commands/notebooklm.md`
- Gemini 통합: `bridge.md`
- 도메인 에이전트: `.claude/agents/line-batch-domain-expert.md`, `settlement-domain-expert.md`
- 토론모드 연계: `90_공통기준/토론모드/CLAUDE.md`
