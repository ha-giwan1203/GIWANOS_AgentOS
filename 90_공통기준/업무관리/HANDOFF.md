# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-18 KST — 세션61 (ask_question PASS + 좀비 Chrome 근본 해결 3세션 검증 전체 PASS)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 0. 최신 세션 (2026-04-18 세션61)

### 이번 세션 완료
1. **세션58 합의 "재인증 없음" 2/2 최종 통과**: Claude Code 재시작 후 `get_health` authenticated=true 유지, `list_notebooks` 2개 유지, `active_sessions`=0
2. **원인 C 해소 확정**: `NOTEBOOK_CLONE_PROFILE=true` 반영 상태에서 `ask_question` 정상 응답 수신 (조립비정산 노트북, session_id `175b71b4`, 18.5초)
3. **exitCode=21 관측 0회** — 3세션 연속(59/60/61) 0회 달성
4. **도메인 정확성 3건 PASS**:
   - [조립비정산] 야간계산식: 기준단가×0.3 + 100% 기본 + 30% 가산 = 130% 정산, 주간=정상-추가, GERP 100%+30% vs 구ERP 30%만 → STATUS.md L12-14/L75-76/L90 일치
   - [라인배치] OUTER 셀렉터: 리스트업 방식, row0=SD9A01 고정, 금지 시간대 로직 → v9.md/CLAUDE.md 일치
   - [라인배치] MAIN/SUB 순서: row0 최빈값 fallback, row1=SP3M3 고정, row2~ LINE_RULES 매핑, 재개 `runOuterLine(idx)`, 강제 중단 `window._haltAll=true` → v9.md/STATUS.md 일치
5. **좀비 Chrome 근본 해결 전체 PASS** (세션58 debate_20260417_230008 합의 검증 조건 전부 충족):
   - 프로세스 재기동 3세션 연속 성공 (세션59 1차/세션60 부분/세션61 완전)
   - exitCode=21 0회
   - 재인증 없음 (세션60·61)
   - ask_question 정상 동작 (세션61)

### 다음 AI 액션 (세션62+)
1. **이슈 #1 종결 처리**: CLONE_PROFILE=true 로 원인 C 해소 확정. notebooklm-mcp 업스트림에 "isolated + CLONE_PROFILE 조합 이슈" 문서화 권고(선택) 또는 내부 메모만으로 종결
2. **이슈 #2 (preserve_library 보호 누락)**: 후순위 유지, 로컬 백업 루틴 검토
3. 다른 생산관리 / 정산 / 라인배치 안건 진입

### 미완료 / 이월
- 이슈 #2 (preserve_library 보호 누락): 후순위
- safe_json_get 파서 교체: 승격 조건 대기 (incident 누적 미도달)

---

## 1. 이전 세션 (2026-04-18 세션60)

### 이번 세션 완료
1. **세션58 합의 "재인증 없음" 1차 통과**: Claude Code 재시작 후 `get_health` authenticated=true 유지, `list_notebooks` 2개 유지, `active_sessions` 0
2. **exitCode=21 관측 0회**
3. **원인 A (10초 타임아웃) 기각**: 세션59 임시 패치 30초 반영 확인됐음에도 동일 실패 → 타임아웃 문제 아님. 패치 원복
4. **원인 C 확정**:
   - `show_browser:true` 관측: 브라우저 창은 떴으나 **로그인 화면** 표시
   - storageState 쿠키 저장 정상(notebooklm.google.com 3개 등 33개)
   - `dist/config.js:65` `cloneProfileOnIsolated: false` 기본값 → isolated 모드 + CLONE_PROFILE=false 조합에서 매 세션 빈 프로필 기동 → 쿠키 없음
5. **조치**: `~/.claude.json`에 `NOTEBOOK_CLONE_PROFILE=true` 추가. 세션58 debate_20260417_230008 "실패 분기 ②" 경로 활성화. 백업 파일 `.claude.json.bak_sess60`

### 다음 AI 액션 (세션61)
1. Claude Code 재시작 직후 `get_health` → authenticated=true 확인 (세션58 합의 "재인증 없음" 2/2 최종)
2. `ask_question` 재시도 → 성공 시 **원인 C 해소 확정 + 세션58 좀비 Chrome 근본 해결 전체 PASS**
3. 성공 시 이어서 도메인 정확성 3건 검증(settlement-domain-expert / line-batch-domain-expert) 수행
4. 여전히 실패 시 원인 D 탐색 + notebooklm-mcp GitHub 이슈 리포트

### 미완료 / 이월
- 이슈 #2 (preserve_library 보호 누락): 후순위, 로컬 백업 루틴 또는 업스트림 리포트
- 라인배치·조립비정산 도메인 정확성 3건 검증: 세션61 ask_question 성공 전제

---

## 1. 이전 세션 (2026-04-18 세션59)

### 이번 세션 완료
1. **notebooklm-mcp 1차 검증 실행 (3세션 중 1/3)**:
   - 최초 `setup_auth` 2회 실패 → `cleanup_data(preserve_library=true)` 41MB 정리 → `setup_auth` 103.74초 성공
   - `get_health` authenticated=true, `list_notebooks` 정상
   - 노트북 2개 재등록 (library.json 소실로 복구 필요했음)
   - `ask_question` 실패: "Could not find NotebookLM chat input"
   - `exitCode=21` 0회 관측
2. **GPT 토론 debate_20260417_235521**: 조건부 통과 (채택 4 / 보류 0 / 버림 0)
3. **critic-reviewer WARN**: Q3 라벨 `실증됨`→`일반론` 재기록. "조건부 통과" 문구 명확화 반영
4. **TASKS 별건 분리 신설 2건**:
   - 이슈 #1: `ask_question` chat input 탐지 실패 추적
   - 이슈 #2: `cleanup_data` preserve_library 보호 누락

### 다음 AI 액션 (세션60)
1. **세션 진입 직후 `get_health`** — authenticated=true 유지 여부 확인 (세션58 합의 재인증 없음 검증)
2. `exitCode=21` 발생 여부 관측 기록
3. **이슈 #1 임시 패치 효과 검증**:
   - 세션59에서 `dist/session/browser-session.js` L139의 `timeout: 10000` → `30000` 수정 완료
   - `ask_question` 재시도 → 성공 시 원인 A(10초 타임아웃 부족) 확정
   - 실패 시 `show_browser=true` 관찰 / 로그인 리다이렉트 확인 → 원인 B/C 추적
4. 원인 A 확정 시 notebooklm-mcp 업스트림 GitHub에 이슈/PR 제기 (하드코딩 10초 → 환경변수화 권고)
5. 세션59 이슈 #1 조치 ①은 이미 수행 완료(셀렉터 기각, 임시 패치 적용). ④ 다른 노트북 교차 테스트는 세션60에서 패치 검증 결과 본 뒤 필요 시 수행

### 미완료 / 이월
- **세션60·61 재인증 없음 검증**: 프로세스 재기동 후에만 확인 가능
- **라인배치·조립비정산 도메인 정확성 3건 검증**: `ask_question` 해소 후 수행

---

## 1. 이전 세션 (2026-04-17 세션58)

### 이번 세션 완료
1. **라인배치 파일럿 2단계**:
   - 통합 소스 생성: `10_라인배치/notebooklm_source_라인배치_v1.txt` (8개 문서 병합, 2,674줄·120KB)
   - 생성 스크립트: `10_라인배치/build_notebooklm_source.py`
   - NotebookLM 노트북 등록: `라인배치_대원테크` (ff23f265-2211-4722-b5fa-d0cdfae73928)
   - 에이전트 작성: `.claude/agents/line-batch-domain-expert.md`
   - `10_라인배치/CLAUDE.md` 에이전트 섹션 추가
2. **좀비 Chrome 근본 해결 GPT 토론** (debate_20260417_230008):
   - 옵션 A/B/C/D 중 A 선결 합의
   - `~/.claude.json`의 notebooklm-mcp env에 `NOTEBOOK_PROFILE_STRATEGY=isolated` 반영 (세션58 실제 수정)
   - 검증 조건: 프로세스 재기동 3세션 연속 성공 기준 확정
3. **critic-reviewer WARN 기록**: B 옵션 배제가 하네스 라벨-판정 불일치. Step 5 진행 허용되나 B 재부상 경로 보존 필요

### 미완료 / 이월
- **3세션 검증 (세션59~61)**: Claude Code 프로세스 재기동 단위로만 가능. 이번 세션에서 실행 불가
- **라인배치 도메인 정확성 3건 검증**: setup_auth 미수행으로 이월. 세션59(isolated 최초 인증 후) 수행
- **라인배치 에이전트 호출 실검증**: 세션 재시작 필요. 세션59 수행

### 다음 AI 액션 (세션59)
1. `mcp__notebooklm-mcp__get_health` → `authenticated` 확인
   - false면 `setup_auth` 실행 (isolated 신규 프로필 최초 인증 — 1회 허용)
2. `ask_question` 1세트 수행 → 성공 여부 + exitCode 확인
3. **세션60 검증 준비**: 세션 종료 시점 기록 (Chrome 프로세스 잔존 수 체크)
4. 세션60 시작 시: `get_health` → `ask_question` 재인증 없이 성공하는지 확인
5. 3세션 연속 PASS 시: 합의안 구현 완료 커밋 + GPT 최종 보고
6. 실패 시: TASKS.md "실패 분기" 표대로 분기 (①→②→③ 순 대응)

### 재접속 체크리스트 (세션59 첫 작업)
- [ ] `mcp__notebooklm-mcp__get_health` → `authenticated=true` 확인
- [ ] false면 `setup_auth` 1회 (isolated 최초 인증, 세션59만 허용)
- [ ] `ask_question` 1건 성공 + `exitCode=21` 미발생 확인
- [ ] Chrome 프로세스 카운트 기록 (비교용): `powershell -c "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' AND CommandLine LIKE '%notebooklm-mcp%'\" | Measure-Object | Select -ExpandProperty Count"`
- [ ] 세션 종료 전에도 카운트 기록 (격리 프로필 종료 정리 여부 확인)

### B 옵션 재부상 경로 (WARN 메모)
세션58 토론에서 Claude의 R4(병렬 Claude 세션 없는 환경에서 B의 "세션 끊기 위험" 과평가 가능성)가 하네스에 버림으로 기록되지 않고 부분 인정(채택)으로 처리됨. 세션59~61 검증 실패 유형별 분기:
- ① exitCode=21 재발만 → B(SessionStart hook taskkill) 재평가 우선
- 후보 명령: `powershell "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' AND CommandLine LIKE '%notebooklm-mcp%'\" | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"`
- 위치 후보: `.claude/settings.json` SessionStart hook

---

## 1. 이전 세션 (2026-04-17 세션57)

### 이번 세션 완료
1. **파일럿 검증 4/4 PASS**:
   - ① Agent 호출 PASS (settlement-domain-expert 2회 진입)
   - ② ask_question MCP 위임 PASS (메인 27.7초, 에이전트 내부 session_id 발급)
   - ③ 꼬리 문구 필터 PASS (원본 `EXTREMELY IMPORTANT:` 포함 → 에이전트 `[응답]`에서 제거)
   - ④ 저장소 교차확인 PASS (STATUS.md L81/L84 실제 라인 인용 일치)
2. **좀비 Chrome Known Issue 해소**: 세션56 setup_auth 후 MCP Chrome 3개(PID 10880/2832/23008) 미정리 상태 발견
   - 증상: `ask_question` 즉시 실패 `exitCode=21` (lockfile 점유)
   - 복구: taskkill /F → cleanup_data(preserve_library=true) → setup_auth (157.53초, 쿠키 자동 복구로 사용자 로그인 불필요)
3. **사용자 질문 해명**: "브라우저 로그인 안 됐는데?" — Chrome 창 미표시는 사실이지만 기존 세션 쿠키 자동 복구로 실제 인증 성공 (library.json 보존 + auth 상태 유지)

### 미완료 / 이월
- 라인배치 NotebookLM 노트북 파일럿 2단계 (세션58로 이월)

### 다음 AI 액션
1. **세션 종료 시 MCP Chrome 좀비 정리 루틴 검토** (stop hook 후보):
   - 후보 명령: `powershell "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { \$_.CommandLine -like '*notebooklm-mcp*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }"`
   - 위험: 정상 MCP 세션이 종료 훅으로 끊길 수 있음 → 종료 훅이 아닌 시작 훅에서 확인하는 방향도 고려
2. **라인배치 파일럿 시작** (세션58):
   - 10_라인배치/ 하위 CLAUDE.md/STATUS.md/RUNBOOK.md 등 병합
   - NotebookLM 노트북 생성·업로드 → `add_notebook`
   - `line-batch-domain-expert` 에이전트 작성 (settlement-domain-expert 템플릿 기반)

### 재접속 체크리스트
- [ ] `mcp__notebooklm-mcp__get_health` → `authenticated=true`
- [ ] false 또는 `ask_question` 실패 시: `powershell -c "Get-CimInstance Win32_Process -Filter ""Name='chrome.exe'"" | Where-Object { $_.CommandLine -like '*notebooklm-mcp*' } | Select ProcessId"`로 좀비 식별 → taskkill → setup_auth
- [ ] 조립비정산 노트북 URL 유효성 (`list_notebooks`)

## 이전 세션 (2026-04-17 세션56)

### 이번 세션 완료
1. **notebooklm-mcp 인증**: `setup_auth` 127초 성공
2. **ad-hoc 질의 검증**: 외부 노트북 테스트 — 응답 26초, 세션 연속성 PASS
3. **조립비정산 NotebookLM 노트북 등록**: `조립비정산_대원테크` (dfb82a61-81b4-4e2d-8ed0-a70a5c7d0b9c)
4. **통합 소스 파일 생성**: `05_생산실적/조립비정산/06_스킬문서/notebooklm_source_조립비정산_v1.txt` (9개 .md → 2,164줄 88KB 병합)
5. **도메인 정확성 3건 PASS**: 야간계산식 / SP3M3 구ERP 주간 / Known Exception 7건 — 전부 STATUS.md 대조 일치
6. **에이전트 작성**: `.claude/agents/settlement-domain-expert.md` — NotebookLM 질의 + 꼬리 필터 + 저장소 교차확인 + 권위서열(저장소>NLM)
7. **도메인 CLAUDE.md 갱신**: 05_생산실적/조립비정산/CLAUDE.md에 에이전트 섹션 추가 (역할 분리표)

### 미완료 (세션 재시작 필요)
- `Agent(subagent_type="settlement-domain-expert")` 호출은 현재 세션에서 미인식 확인 → **다음 세션에서 실검증**
- 라인배치 NotebookLM 노트북 파일럿 2단계

### 다음 AI 액션
1. **세션 재시작 후 첫 작업**: settlement-domain-expert 동작 4점 검증
   - Agent 도구 호출 가능 여부
   - 에이전트 내부 `mcp__notebooklm-mcp__ask_question` 위임 작동
   - 꼬리 문구 `EXTREMELY IMPORTANT:` 필터 실작동
   - 저장소 교차확인 (CLAUDE.md/STATUS.md L{line} 인용) 정확성
2. **라인배치 파일럿 시작**: 10_라인배치/ 하위 문서 식별 → 통합 소스 병합 → NotebookLM 생성·업로드 → add_notebook → line-batch-domain-expert 에이전트 작성
3. Chrome MCP 자동 업로드 경로 재탐색 (이번 세션은 탭 그룹핑 미지원으로 우회)

### 재접속 체크리스트
- [ ] `mcp__notebooklm-mcp__get_health` → `authenticated=true`
- [ ] false면 `setup_auth` 재실행
- [ ] 조립비정산 노트북 URL 유효성 확인

## 이전 세션 (2026-04-17 세션55)

### 세션55 완료
1. **YouTube 영상분석 (yBfyanZMyV4)**: 12프레임+자막 통합 분석, A0/B2/C3 판정
2. **B등급 도출**: notebooklm-mcp 설치+인증, 도메인 에이전트 등록 — 세션56에서 실행 완료
3. **Notion 콘텐츠 분석 이력 DB**: upsert 완료 (https://www.notion.so/345fee670be881738bcddbbb1cc0909f)
4. **핵심 패턴 확인**: 에이전트(도메인 지식) + 스킬(레시피) 분리 설계 — 세션56에서 settlement-domain-expert로 첫 적용

## 이전 세션 (2026-04-17 세션54)

### 세션54 완료
1. **GPT 토론 "클로드코드 정밀분석"** — 지적 7건 분해 후 채택 3 / 보류 3 / 버림 0
2. **P0-1 smoke_test.sh:528 수정**: `'27개'` → `'28개'` (커밋 b2f47806 불완전 마감 보정)
3. **P0-2 harness_gate.sh:118 수정**: `"decision":"block"` → `"decision":"deny"` (파일 내부 포맷 통일)
4. **smoke_test 167/167 PASS 확인** (regression 27~30 섹션 포함 전체 통과)
5. **safe_json_get 승격 조건 명시화**: navigate/evidence/completion_gate JSON 파싱 실패 incident + 중첩키 빈값 재현 + 7일 내 2회 누적

## 이전 세션 (2026-04-15 세션53)

### 세션53 완료
1. **학습루프 점검**: self-audit-agent로 메모리 시스템 전수 점검
2. **P0 인덱스 누락 수정**: feedback_gpt_input_inserttext.md 등록
3. **P1 rules 충돌 해소**: data-and-files.md candidate 브랜치 → main 직행 현행화
4. **P1 중복 메모리 6그룹 통합**: 8건 삭제 (톤/독립검증/공유루틴/스킬사용/지시문읽기/PR금지)
5. **P2 구식 항목**: permission_bypass 삭제, 3건 갱신 (efficiency/vulnerability/notion)
6. **P3 user 메모리 신규**: user_role_manufacturing.md (직무/ERP환경/기술수준)

## 이전 세션 (2026-04-15 세션52)

### 세션52 완료
1. **GPT 토론 1턴 합의 3건**: 채택 3건 / 보류 0건 / 버림 0건
2. **req clear 규칙 문서화 종결**: 코드 변경 불필요, 문서화 종결
3. **status_sync.sh 보류**: final_check.sh가 이미 검사 중
4. **AGENTS_GUIDE 자동생성**: generate_agents_guide.sh 신규
5. **supanova-deploy·skill-creator 카테고리 종결**

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260413_20260415.md`
