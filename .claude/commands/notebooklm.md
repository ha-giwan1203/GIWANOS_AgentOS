# /notebooklm — NotebookLM 컨트롤 레이어

NotebookLM ↔ Gemini 통합을 일관되게 사용하기 위한 단일 진입점.
**메인 채널은 Gemini.** NotebookLM MCP는 인증·라이브러리·소스 근거 인용용 백엔드.

> 본 커맨드는 `90_공통기준/notebooklm/registry.yaml` v2 스키마를 따른다.
> v2 필드: `name`, `gemini_url`, `notebooklm_url`, `uuid`, `status` (primary | legacy), `domain`, `agent`, `topics`, `primary_use`, `sources`, `active`

## 인자
- `$ARGUMENTS`: 서브커맨드 + 인자
  - `list` — 등록된 노트북 목록 (registry.yaml 기준)
  - `health` — MCP 인증·세션·자산 상태 점검
  - `query <도메인|이름> <질문>` — NotebookLM MCP 직접 질의 (소스 근거 인용)
  - `ask <도메인|이름> <질문>` — Gemini 노트북 페이지 직접 진입 질의 (메인 흐름)
  - `sync` — registry ↔ MCP 라이브러리 차이 보고 (read-only)
  - `register <name> <gemini_url> <notebooklm_url> <domain>` — registry.yaml에 새 노트북 추가

## 도메인 라우팅

도메인 키 또는 노트북 이름으로 라우팅. registry.yaml `domain` 필드 매칭.
동일 domain 내 `status=primary` 항목 우선. primary 미존재 시 legacy fallback.

| 도메인 키 | primary 노트북 | legacy 노트북 | 에이전트 |
|----------|--------------|--------------|---------|
| `line-batch` | 라인배치_대원테크_v2 | 라인배치_대원테크 | line-batch-domain-expert |
| `settlement` | 조립비정산_대원테크_v2 | 조립비정산_대원테크 | settlement-domain-expert |

## 실행 절차

### 0. registry 로드 (모든 서브커맨드 공통)
```
Read 90_공통기준/notebooklm/registry.yaml
```
- `name` / `gemini_url` / `notebooklm_url` / `uuid` / `status` / `domain` / `active` 파싱
- `active=false` 항목은 라우팅 대상에서 제외
- 도메인 매칭 시 `status=primary` 우선

### 1. `list`
1. registry.yaml 파싱
2. 표 출력: `name` / `domain` / `status` / `topics` / `sources` / `active`
3. primary와 legacy 그룹 분리 표시

### 2. `health`
1. `bash 90_공통기준/notebooklm/health.sh` 실행 → 정적 자산 점검 결과 받음
2. `mcp__notebooklm-mcp__get_health` 호출 → authenticated / active_sessions 확인
3. authenticated=false 시 `mcp__notebooklm-mcp__setup_auth` 안내 (자동 실행 금지)
4. `mcp__notebooklm-mcp__list_notebooks` 호출 → registry `notebooklm_url`과 차이 비교
5. 종합 보고:
   - 자산 PASS/WARN/FAIL
   - 인증 상태
   - registry vs MCP 차이 (있으면 sync 권고)
   - primary 노트북 sources 필드 0인 경우 업로드 필요 경고

### 3. `query <도메인|이름> <질문>`

> NotebookLM MCP 직접 호출. 소스 근거가 포함된 인용 응답 받기 위함.
> primary·legacy 어느 쪽이든 가능. shared(legacy)도 MCP 직접 호출은 작동.

1. 도메인/이름으로 registry에서 노트북 항목 찾기 (active=true 필터)
2. 도메인 에이전트가 정의되어 있으면 → `Agent(subagent_type=<agent>, prompt=<질문>)` 위임 (메인 컨텍스트 보호)
3. 없으면 직접:
   - `mcp__notebooklm-mcp__ask_question(notebook_url=<registry.notebooklm_url>, question=<질문>)`
4. 응답 출력 (소스 근거·인용 marker 포함)

### 4. `ask <도메인|이름> <질문>` — 메인 흐름

> Gemini 노트북 페이지 직접 진입 (`gemini.google.com/notebook/notebooks/<UUID>`).
> shared(legacy) 노트북은 Gemini 미노출 → primary만 사용 가능. legacy 도메인 매칭 시 자동 fallback to query.

1. registry에서 `domain` 매칭 → `status=primary` 항목 추출
   - primary 미존재 → "primary 노트북 없음. /notebooklm query 로 fallback 권고" 안내 후 종료
2. `gemini_url` 추출 (또는 `https://gemini.google.com/notebook/notebooks/<uuid>` 조립; URL `/` 인코딩 주의 — 직접 navigate 시 `notebooks%2F<uuid>` 사용)
3. `mcp__chrome-devtools-mcp__list_pages` → 기존 노트북 탭 확인. 없으면 `new_page(url=<gemini_url>)`
4. `select_page(pageId, bringToFront=true)` 활성화
5. `/gemini-send` 절차 그대로 호출 (입력창 `.ql-editor.ql-blank.textarea.new-input-ui` 동일)
6. `/gemini-read`로 응답 수령

### 5. `sync`

> registry ↔ MCP 라이브러리 차이를 read-only로 보고. 자동 수정 안 함.

1. `mcp__notebooklm-mcp__list_notebooks` → MCP 측 노트북 목록
2. registry.yaml → `notebooklm_url` 기반 매칭 (UUID 비교)
3. 차이 분류:
   - **registry에만 있음** (status=primary) → MCP `add_notebook`은 자동 안 함 (shared 처리 위험). 사용자 안내만
   - **MCP에만 있음** → registry 추가 필요 (사용자 확인 후 register 권고)
   - **양쪽 일치** → OK
4. URL·UUID 불일치 항목 별도 강조
5. legacy 항목 중 sources 이전 완료 후 폐기 후보 안내

### 6. `register <name> <gemini_url> <notebooklm_url> <domain>`

> Gemini에서 만든 새 노트북을 registry에 등록. v2 스키마 강제.

1. URL 형식 검증:
   - `gemini_url`: `https://gemini.google.com/notebook/notebooks/<UUID>` 패턴
   - `notebooklm_url`: `https://notebooklm.google.com/notebook/<UUID>` 패턴
   - 두 URL의 UUID가 일치해야 함 (양방향 동기화 검증)
2. registry.yaml 기존 항목과 중복 검사 (name 또는 uuid)
3. 신규 항목 추가 (Edit tool):
```yaml
  - name: <name>
    gemini_url: <gemini_url>
    notebooklm_url: <notebooklm_url>
    uuid: <UUID>
    status: primary
    domain: <domain>
    agent: null   # 도메인 에이전트 있으면 설정
    topics: []
    primary_use: TBD
    sources: 0    # 업로드 후 갱신
    active: true
```
4. 사용자에게 topics·primary_use·소스 업로드 후속 안내

## 주의사항
- [NEVER] registry.yaml과 MCP 라이브러리를 자동 동기화하지 않음 — sync는 보고만
- [NEVER] 노트북 URL을 registry 외부에 하드코딩 금지
- [NEVER] MCP `add_notebook` 자동 호출 금지 — shared 노트북 자동 생성 부작용 (Gemini 미노출 원인)
- [MUST] 도메인 한정 질의는 도메인 에이전트 경유 — 메인 컨텍스트 보호
- [MUST] CDP Chrome (포트 9222) 미기동 시 ask 흐름 불가 → 토론모드 자동 기동 정책 따름
- [MUST] ask는 status=primary 노트북에만 적용. legacy는 query로만
- 인증은 사용자 액션 필요 — Claude가 자동 인증 시도 금지

## 관련 문서
- 도메인 진입: `90_공통기준/notebooklm/CLAUDE.md`
- Gemini 통합 절차 + 셀렉터: `90_공통기준/notebooklm/bridge.md`
- 레지스트리: `90_공통기준/notebooklm/registry.yaml` (v2 스키마)
- 헬스 스크립트: `90_공통기준/notebooklm/health.sh`
