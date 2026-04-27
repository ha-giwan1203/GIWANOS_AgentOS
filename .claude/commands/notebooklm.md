# /notebooklm — NotebookLM 컨트롤 레이어

NotebookLM ↔ Gemini 통합을 일관되게 사용하기 위한 단일 진입점.
**메인 채널은 Gemini.** NotebookLM MCP는 인증·라이브러리·소스 근거 인용용 백엔드.

## 인자
- `$ARGUMENTS`: 서브커맨드 + 인자
  - `list` — 등록된 노트북 목록 (registry.yaml 기준)
  - `health` — MCP 인증·세션·자산 상태 점검
  - `query <도메인|이름> <질문>` — NotebookLM MCP 직접 질의 (소스 근거 인용)
  - `ask <도메인|이름> <질문>` — Gemini 사이드패널 모드 질의 (메인 흐름)
  - `sync` — registry ↔ MCP 라이브러리 차이 보고 (read-only)
  - `register <name> <url> <domain>` — registry.yaml에 새 노트북 추가

## 도메인 라우팅

도메인 키 또는 노트북 이름으로 라우팅. registry.yaml `domain` 필드 매칭.

| 도메인 키 | 노트북 | 에이전트 |
|----------|--------|---------|
| `line-batch` | 라인배치_대원테크 | line-batch-domain-expert |
| `settlement` | 조립비정산_대원테크 | settlement-domain-expert |

## 실행 절차

### 0. registry 로드 (모든 서브커맨드 공통)
```
Read 90_공통기준/notebooklm/registry.yaml
```
- 도메인·이름·URL·active 상태 파악
- active=false 노트북은 라우팅 대상에서 제외

### 1. `list`
1. registry.yaml 파싱
2. 표 출력: 이름 / 도메인 / topics / active

### 2. `health`
1. `bash 90_공통기준/notebooklm/health.sh` 실행 → 정적 자산 점검 결과 받음
2. `mcp__notebooklm-mcp__get_health` 호출 → authenticated / active_sessions 확인
3. authenticated=false 시 `mcp__notebooklm-mcp__setup_auth` 안내 (자동 실행 안 함 — 사용자 인증 필요)
4. `mcp__notebooklm-mcp__list_notebooks` 호출 → registry와 차이 비교
5. 종합 보고:
   - 자산 PASS/WARN/FAIL
   - 인증 상태
   - registry vs MCP 차이 (있으면 sync 권고)

### 3. `query <도메인|이름> <질문>`

> NotebookLM MCP 직접 호출. 소스 근거가 포함된 인용 응답 받기 위함.

1. 도메인/이름으로 registry에서 노트북 항목 찾기
2. 도메인 에이전트가 정의되어 있으면 → `Agent(subagent_type=<agent>, prompt=<질문>)` 위임 (메인 컨텍스트 보호)
3. 없으면 직접:
   - `mcp__notebooklm-mcp__select_notebook(query=<noteobok_name>)`
   - `mcp__notebooklm-mcp__ask_question(question=<질문>)`
4. 응답 출력 (소스 근거·인용 marker 포함)

### 4. `ask <도메인|이름> <질문>`

> Gemini 메인 채널. 사이드패널에서 노트북 활성화 후 질의.

1. registry에서 `gemini_label` 추출
2. **사이드패널 통합 가능 여부 확인** (첫 사용 시):
   - `take_snapshot`으로 사이드패널 셀렉터 실측 → `bridge.md` 셀렉터 메모 갱신
   - 통합 미반영(롤아웃 미완) 시 → B 흐름(MCP 응답을 Gemini 챗에 주입)으로 fallback
3. **A 흐름 (사이드패널 활성)**:
   - `/gemini-send` 진입 절차 (1-A ~ 1-D)
   - 사이드패널에서 `gemini_label` 노트북 클릭 활성화
   - `/gemini-send`로 질문 전송
   - `/gemini-read`로 응답 수령
4. **B 흐름 (Fallback — bridge.md "B" 절차)**:
   - `mcp__notebooklm-mcp__ask_question` 응답 발췌 → `[노트북 근거]` 블록으로 Gemini에 주입
   - 일반 `/gemini-send` 경로로 전송

### 5. `sync`

> registry ↔ MCP 라이브러리 차이를 read-only로 보고. 자동 수정 안 함.

1. `mcp__notebooklm-mcp__list_notebooks` → MCP 측 노트북 목록
2. registry.yaml → 등록된 노트북 목록
3. 차이 분류:
   - **registry에만 있음** → MCP에 add 필요 (사용자 안내)
   - **MCP에만 있음** → registry 추가 필요 (사용자 확인 후 register 권고)
   - **양쪽 일치** → OK
4. URL·이름 불일치 항목 별도 강조

### 6. `register <name> <url> <domain>`

1. URL 형식 검증: `https://notebooklm.google.com/notebook/<UUID>` 패턴
2. registry.yaml 기존 항목과 중복 검사 (name 또는 url)
3. 신규 항목 추가 (Edit tool):
```yaml
  - name: <name>
    url: <url>
    gemini_label: <name>
    domain: <domain>
    agent: null
    topics: []
    primary_use: TBD
    sources: TBD
    active: true
```
4. (선택) `mcp__notebooklm-mcp__add_notebook` 호출 — MCP 라이브러리에도 등록
5. 사용자에게 topics·primary_use 채울지 후속 질문

## 주의사항
- [NEVER] registry.yaml과 MCP 라이브러리를 자동 동기화하지 않음 — sync는 보고만
- [NEVER] 노트북 URL을 registry 외부에 하드코딩 금지
- [MUST] 도메인 한정 질의는 도메인 에이전트 경유 — 메인 컨텍스트 보호
- [MUST] CDP Chrome (포트 9222) 미기동 시 ask 흐름 불가 → 토론모드 자동 기동 정책 따름
- 인증은 사용자 액션 필요 — Claude가 자동 인증 시도 금지

## 관련 문서
- 도메인 진입: `90_공통기준/notebooklm/CLAUDE.md`
- Gemini 통합 절차: `90_공통기준/notebooklm/bridge.md`
- 레지스트리: `90_공통기준/notebooklm/registry.yaml`
- 헬스 스크립트: `90_공통기준/notebooklm/health.sh`
