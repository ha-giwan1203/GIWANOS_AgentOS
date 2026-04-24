# 업무리스트 작업 목록

> **이 파일은 AI 작업 상태의 유일한 원본이다.**
> 완료/미완료/진행중/차단 상태는 이 파일에만 기록한다.
> STATUS.md·HANDOFF.md·Notion은 이 파일을 참조하며, 독립적으로 상태를 선언하지 않는다.
> 판정 우선순위: TASKS.md > STATUS.md > HANDOFF.md > Notion
> 도메인 하위 `TASKS.md`는 해당 도메인 내부 실행 목록만 관리한다. 저장소 전체 우선순위·완료판정·인수인계 기준은 항상 이 파일이다.
>
> **주의: 이 파일은 현업 업무 전체 목록의 원본이 아니다.**
> 실제 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본은 `90_공통기준/업무관리/업무_마스터리스트.xlsx`이다.
> 이 파일은 그중 AI가 수행해야 하는 자동화·문서화·구조 개편·검토·인수인계 작업만 관리한다.

최종 업데이트: 2026-04-24 KST — 세션105 3자 토론 Round 1 + chrome-devtools-mcp CDP Chrome 연결 완료 + 4개 스킬 마이그레이션

## 세션105 (2026-04-24 저녁) — 시스템 개선 3자 토론 + 탭 전환 근본 해결

**[진행중] 3자 토론 Round 1 — 세션103 이월 의제 3건**
- 로그: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/`
- Q1 조건부 격상: GPT=C(포기) / Gemini=B(실측) — 불일치, Round 2 재검증 예정
- Q2 실증됨 라벨 엄격화: GPT=A / Gemini=A — 합의 (증거 필수 규칙)
- Q3 incident 110건 대응: GPT=A / Gemini=A — 합의 (즉시 /auto-fix 1차 분류)
- 다음: Round 2 (Q1 집중) — chrome-devtools-mcp `select_page`로 탭 전환 가능

**[완료] 탭 전환 근본 해결 — chrome-devtools-mcp 병행 설치**
- 원인: Claude in Chrome MCP가 CDP `Target.activateTarget` / `Page.bringToFront` 차단
- Step 1 ✅ `chrome-devtools-mcp` user scope 등록
- Step 2 ✅ CDP Chrome 포트 9222 LISTENING
  - **주의**: Chrome M136+ 보안 강화로 기본 프로필에서 CDP 사용 금지 → 별도 프로필 `C:\temp\chrome-cdp` 사용
  - 기본 Chrome과 CDP Chrome 병행 기동 중
- Step 3 ✅ chrome-devtools-mcp 도구 로드 + 포트 9222 연결 확인 (ToolSearch로 본 세션 로드 완료, 세션 재시작 불필요)
- ChatGPT·Gemini 양측 CDP Chrome에서 로그인 완료 (재로그인 1회성 비용)

**[완료] 4개 스킬 chrome-devtools-mcp 마이그레이션 (사용자 지시 예외 / D안 선례 준용)**
- `.claude/commands/gpt-send.md`, `gpt-read.md`, `gemini-send.md`, `gemini-read.md` 전면 재작성
- `90_공통기준/토론모드/CLAUDE.md` 탭 throttling 대응 섹션 + Chrome MCP 금지 범위 갱신
- 핵심 변경:
  - `tabs_context_mcp` → `list_pages` / `tabs_create_mcp` → `new_page`
  - `navigate(url, tabId)` 재호출 hack → `select_page(pageId, bringToFront=true)` (CDP 네이티브)
  - `javascript_tool` → `evaluate_script`
  - `get_page_text`/`find`/`computer` → `take_snapshot`/`click`/`fill` (필요 시만)
- 상태 파일 `gpt_tab_id`·`gemini_tab_id` 내용 의미 변경: 문자열 tabId → 정수 pageId



> **메타 억제 기준**: `.claude/state/meta_freeze.md` — **해제됨** (2026-04-23, incident 52건)

---

## 세션104 (2026-04-24 저녁) — /d0-plan 야간 실운영 + xlsx 포맷 근본 수정

**[완료] SP3M3 야간 15건 실운영 반영**
- 파일: `SP3M3_생산지시서_(26.04.25).xlsm` 출력용 야간 섹션 → 15건 추출
- Phase 3 업로드 → Phase 4 서열 배치 15건 → Phase 5 MES 전송 (rsltCnt=750) ✅

**[완료] xlsx 포맷 버그 근본 해결 — openpyxl → Excel COM**
- 증상: openpyxl로 생성한 xlsx 업로드 시 ERP 서버가 COL2(제품번호) 빈값으로 파싱, 15건 전부 ERROR_FLAG=Y
- 원인: OOXML 내부 구조(sharedStrings, cell type 속성, 시트 XML 네임스페이스) 차이
- 해결: `make_upload_xlsx`를 `win32com.client(Excel.Application)` 기반으로 교체. 템플릿 복사 후 Excel이 직접 저장
- 템플릿: `90_공통기준/스킬/d0-production-plan/template/SSKR_D0_template.xlsx` (ERP 양식다운로드본)
- `.gitignore`에 `!90_공통기준/스킬/d0-production-plan/template/*.xlsx` 예외 허용 추가

**[완료] Phase 6 verify_smartmes 날짜 버그 수정**
- 기존: `run_session_line`이 prod_date 단일로 검증
- 수정: `verify_prod_date` 파라미터 추가 — SP3M3 야간은 야간 시작일(target_file_date-1)로 SmartMES 조회
- main session 분기에서 각각 명시 전달

**[완료] 팝업 재사용 로직 우선 배치**
- 기존: overlay 감지 시 reload가 먼저 → 팝업 iframe이 사라져 매번 새로 오픈 시도
- 수정: 팝업 iframe 검사를 앞에 배치 — 있으면 재사용, 없을 때만 overlay 체크/reload
- 연속 실행 시(dry-run → live) Chrome이 팝업 열린 채 유지되어도 정상 동작

**[완료] SKILL.md v2 갱신**
- Python 의존성에 `pywin32` + Microsoft Excel 설치 필요 명시
- Phase 2 10번 Excel COM 강제 경고 추가
- 핵심 주의사항 0번(최상단)에 openpyxl 생성 금지 경고

**[대기] 후속**
- SD9A01 OUTER 저녁 세션 실 검증 (내일 저녁 `--dry-run` 먼저)
- `D0_SP3M3_Evening` 스케줄 추가 검토 (SP3M3 저녁 세션도 자동화)

---

## 세션102 (2026-04-24) — auto_commit_state 운영 계약 보강 (3자 토론 [3way])

**[완료] P-1 protected_assets.yaml 등록**
- `90_공통기준/protected_assets.yaml` Stop 계열 블록에 `auto_commit_state.sh` 추가
- class: guard, removal_policy: replace-only
- 사유: 세션101 GPT 평가 L-1 — 신규 Stop hook이 보호 레지스트리 미등재 (SPOF-4)

**[완료] P-2 README Failure Contract 등재**
- `.claude/hooks/README.md` Failure Contract 표에 `auto_commit_state.sh` 추가
- 정책: fail-open (advisory) + AUTO 패턴 한정 + final_check FAIL 시 incident 기록 후 자동 commit/push 차단
- 사유: 세션101 GPT 평가 L-2 — 운영 계약 문서화 누락

**[완료] hook_common 계측 적용 (커밋 2 분리)**
- `.claude/hooks/auto_commit_state.sh` source hook_common.sh + hook_timing_start/end + hook_log + hook_incident
- 합의 본질 구현 (hook_advisory wrapper 직접 호출 대신 내부 함수 활용 — 다단계 로직 흐름 보존)
- 기록 확인: timing/incident_ledger/hook_log 정상 동작 (final_check FAIL 테스트 PASS)
- 분리 사유: 사용자 지침 "한 곳 수정이 다른 곳을 무너뜨림" 반영. 실행 파일 변경은 회귀 추적 단위 분리

**[합의 결과] 3자 토론 (Round 1, pass_ratio=1.0)**
- Q1: A안 (3/3) — Stop 블록 추가
- Q2: B안 (3/3) — incident 기록 + push 차단
- Q3: A안 (2/3) — hook_advisory 래핑 (Gemini C안 hook_gate는 별도 의제 이월)
- Q4: B안 (2/3) — 분리 커밋 (Claude 입장 변경, 사용자 지침 반영)
- 로그: `90_공통기준/토론모드/logs/debate_20260424_132813_3way/`

**[완료] GPT 재평가 P-1 반영 (settings.local 1회성 제거)**
- `.claude/settings.local.json:34` `Bash(python create_sp3m3_process_eval.py)` 제거 — SP3M3 평가서 생성 1회용, 재사용 근거 없음
- GPT 재평가 판정: L-1 실증됨, 심각도 중

---

## 세션103 (2026-04-24) — Stop hook 등급 체계 재검토 [3way]

**[완료] advisory 유지 + stderr 가시성 강화**
- 3자 토론 (GPT gpt-5-5-thinking + Gemini gemini-2.5-pro) Round 1 pass_ratio=0.75 합의
- Q1: B안 채택 — 즉시 hook_gate 격상 반대. advisory 유지 + 경고 포맷 개선
- Q2: B안 채택 — exit 2 부작용(일시 오류 무한 블록) > 이점. advisory + 가시성 우선
- 변경: `auto_commit_state.sh:87` 박스형 ⛔ 경고 포맷 적용 (실행 흐름 미변경, A 분류)
- 로그: `90_공통기준/토론모드/logs/debate_20260424_152100_3way/`

**[폐기] 조건부 격상 설계** (세션103 3way 채택 → 세션103 폐기)
- 사유: advisory + commit/push 차단 + incident + stderr 박스 경고로 이미 실용적 보호 충분
- 반복 구조적 FAIL 실발생 빈도 낮음. 구현 복잡도(카운트 추적·세션 경계·임계값) > 실효
- 임계값 오설정 시 과도 차단 또는 유명무실. 제조업 세션 중단 리스크

**[폐기] P-4 wrapper drift 감시** (세션101 이월 → 세션103 폐기)
- 사유: hook_common wrapper 적용 hook 1개(debate_verify)뿐, 감시 대상 부재
- 세션102 실적용에서 wrapper 대신 내부 함수 활용 방식 채택 (다단계 로직 보존)
- 일괄 적용 계획 없이 drift 감시만 신설은 유효하지 않음

---

## 다음 세션 의제 — SD9A01 공정별 숙련도 평가서 작성 (대기 중)

**[대기] SD9A01 공정별 숙련도 평가서 작성 (SP3M3 패턴 복제)**
- 계획서: `01_인사근태/숙련도평가/SD9A01_작업계획.md`
- 대상: SD9A01 라인 10공정, 개인 평가서 24명 (주간 13+야간 11, SD9M01 라인코드)
- **Phase 0 선행**: 작업표준서 통합 필요 (180706 Rev.16 + 260101 Rev.16 → 통합본 1개)
- Phase 1: 공정별 양식 10개 (SP3M3 v4 기반)
- Phase 2: 개인별 파일 24개 (SP3M3 personal_v2 기반)
- 재사용 자산: 샘플 양식, 스크립트 2종, 구조 패턴
- 세션 시작 시 사용자 확인: 작업표준서 통합 방식 (A=최신단독/B=자동병합/C=수기)

---

## 세션102 (2026-04-24) — SP3M3 공정별 숙련도 평가서 신규 작성

**[완료] SP3M3 공정별 숙련도 평가서 6개 파일 생성**
- 위치: `01_인사근태/숙련도평가/SP3M3_공정별 평가서/`
- 파일: 공정10/11/91/140/340/430 각 개별 xlsx
- 샘플 양식(`공정 평가서표준_SP3M3_샘플.xlsx`) 레이아웃/스타일 유지
- 전문강화 섹션(행13~21) 재구성:
  - 작업표준서 기준 5항목 (행13~17) — 출처: `SP3M3_작업표준서_200730_R1.xlsx`
  - 관리계획서 기준 4항목 (행18~21) — 출처: `SP3M3_관리계획서_대원테크.xlsx`
- 평가기준 Q/U/Y 열(100%/80%/미달) 각 항목별 의미 맞게 재작성
- 생성 스크립트: `01_인사근태/숙련도평가/생성스크립트/create_sp3m3_v4.py`
- 공정명 기준 매핑(번호 기준 아님): 공정140→시트130, 공정340→시트330 등 확인

---

## 세션101 (2026-04-24) — /d0-plan 스킬 실운영 검증 + 자동 스케줄링

**[완료] SP3M3 주간 15건 실운영 반영 (아침 세션 첫 실행)**
- 파일: `SSKR D+0 추가생산 Upload.xlsx` (생산일 2026-04-24, 15건)
- Phase 3 업로드 → Phase 4 서열 배치 15건 → Phase 5 MES 전송 (rsltCnt=750) → Phase 6 SmartMES 순서 일치 ✅

**[완료] 스킬 런타임 버그 수정 3건**
- `navigate_to_d0`: OAuth 리다이렉트 완료 대기 추가 (goto 네비게이션 충돌 해소)
- `--xlsx` 옵션: 외부 엑셀 파일 직접 지정 모드 (Phase 1 추출 건너뜀)
- `--skip-upload` 옵션: Phase 3 업로드 건너뜀 (이미 상단 등록된 경우 Phase 4부터)
- s_grid 대기 조건 완화: `>= 5행` → 고정 3초 (주간 초기 빈 서열 대응)
- 팝업 오픈 재시도 (최대 3회)

**[완료] 자연어 트리거 키워드 대폭 확장 + 금지사항 명시**
- SKILL.md description: "등록/반영/올려/업로드" × "주간/야간/D0/SP3M3/SD9A01/아우터" 조합
- Excel 직접 열기 / 모니터 전환 / ERPSet Client(javaw.exe) / computer-use 마우스 조작 **금지** 명시
- `.claude/commands/d0-plan.md` 자연어 트리거 섹션 추가
- 배경: Claude Desktop + computer-use 세션에서 스킬 미인식 + 엉뚱한 경로 탐색 사건

**[완료] Windows 작업 스케줄러 자동 실행 등록**
- 작업명: `D0_SP3M3_Morning`, 매주 월~토 07:10 KST, 일요일 제외
- 실행 계정: InteractiveToken (사용자 로그온 시에만, pyautogui GUI 필요)
- 래퍼: `90_공통기준/스킬/d0-production-plan/run_morning.bat`
- 로그: `06_생산관리/D0_업로드/logs/morning_YYYYMMDD.log` (일자별 누적)
- 첫 자동 실행: 2026-04-25 토요일 07:10

**[완료 추가] 하이브리드 자동 커밋 hook 신설 (세션101)**
- `.claude/hooks/auto_commit_state.sh` — Stop 이벤트 5번째 등록 (hooks 31→32)
- AUTO: TASKS/HANDOFF/STATUS/notion_snapshot/finish_state/write_marker → 자동 커밋+푸시
- MANUAL: 코드/스킬/설정 → stderr 리마인더만 (`/finish` 또는 수동 커밋 권장)
- 안전장치: main 브랜치만, 민감패턴 스캔, push 60s timeout soft-fail

**[완료 추가] GPT 정밀평가 3자 토론 반영 (세션101, 2026-04-24)**
- 3자 토론 (Claude × GPT 웹 × Gemini API 2.5-pro) — `/debate-mode` 변형 (Gemini는 API 대체, 사용자 지시)
- 합의 결과: 3건 채택 / 3건 반려(GPT 과잉 경보)
- **P-1 (A-수정안 GPT 제안)**: `.claude/hooks/auto_commit_state.sh` git commit 직전 `final_check.sh --fast` 인라인 호출 추가 — Stop hook 자동 커밋도 교차검증 통과 시에만 진행 (commit_gate 우회 해소)
- **P-2**: `.claude/settings.local.json` 절대경로 3건 (L21/L29/L32) → 상대경로화
- **P-3**: `.claude/hooks/list_active_hooks.sh:9` 주석 "(31)" → "(32)" drift 정정
- **반려**: A2-1(d0 SKILL ↔ /d0-plan command wrapper 정상), A2-5(6건 command+skill pair wrapper 정상), 리포트 "임시검토"(환경 한계)
- **이월 (P-4 신규)**: slash 진입 vs 자연어 진입 drift 감시 — `.claude/hooks/skill_drift_check.sh` 기능 확장 또는 별도 `wrapper_consistency.py`
- 플랜 파일: `C:/Users/User/.claude/plans/splendid-coalescing-snowflake.md` (보존)
- 검증: smoke_fast 11/11 PASS, doctor_lite OK, hook count 32
- **GPT 조건부 통과 지적 반영 (2건 제거)**: `Bash(sort -k6,7)` 일회성 제거, `Bash(PYTHONIOENCODING=utf-8 python3 90_공통기준/스킬/daily-routine/run.py)` L14와 완전 중복이라 제거. 유지 3건(mcp__Claude_in_Chrome__read_page/find, list_active_hooks.sh --count)은 3자 토론·검증 도구로 반복 사용 근거 있음

**[대기] 후속**
- 4/25~28 자동 실행 관찰 (성공률/로그 이상/중복 저장 등)
- SD9A01 OUTER 저녁 세션 실 검증 (내일 저녁 `--dry-run` 먼저)
- 안정화 후 grade B → A 격상

---

## 세션100 (2026-04-23) — GPT 프로토콜 스킬 신설 (클로드코드 정밀평가)

**[완료] `90_공통기준/업무관리/gpt-skills/` 신설 + 프로토콜 1건 등록**
- 배경: 사용자가 GPT에게 매번 장문으로 "클로드코드 전체 상태 정밀평가"를 입력 → 평가 깊이 불일치, 개선안이 전체 구조를 안 봐서 수정하면 다른 곳이 터지는 반복 문제
- 신규 파일 3건:
  1. `90_공통기준/업무관리/gpt-skills/claude-code-analysis.md` — 트리거 4종 + 7서브시스템(S1~S7) + 5축(A1~A5) + R1~R5 영향반경 필드 + 엄격 템플릿
  2. `90_공통기준/업무관리/gpt-skills/README.md` — 폴더 목적·추가 등록 규칙
  3. `90_공통기준/업무관리/gpt-instructions.md` — "GPT 프로토콜 스킬" 섹션 추가 (도메인 진입 프로토콜 아래)
- 설계 원칙: 大→中→小 계층 순서 고정 + 각 개선안에 R1~R5 영향반경 의무 첨부 (누락 시 자동 강등)
- Claude Code 쪽 hook/skill/settings/CLAUDE.md 변경 **없음** (B분류 구조 변경 아님, 2자 종결 경로)
- 플랜: `.claude/plans/gpt-steady-wreath.md` (사용자 승인 후 구현)
- 검증: 커밋 푸시 후 ChatGPT에서 "클로드코드 정밀평가" 실입력 테스트 예정
- GPT 프로젝트 업로드: 사용자 지시로 ChatGPT 프로젝트에 직접 업로드 (세션 내 후속 작업)

---

## 세션99 (2026-04-23) — AGENTS_GUIDE hooks 파서 버그 수정 (2자 토론 통과 — GPT 최종 PASS)

**[완료] GPT 최종 판정 PASS** (커밋 fa4face2 실물 대조)
- 로그: `90_공통기준/토론모드/logs/debate_20260423_212854/round2_gpt_final.md`
- 보강 3건 실물 반영 확인 + 상태 원본 충돌 없음 + 회귀 PASS
- 별건(README M5, SETTINGS dead assignment) PASS 막지 않음 확인. 세션99 종결

**[완료] final_check 4.5 섹션 신설 — HANDOFF 헤더-본문 판정 레이블 정합 advisory**
- 사용자 지시 예외(D안) 즉시 적용. B 분류 구조 변경이나 "지금바로 적용해라" 명시 지시로 A 강등
- 증상: Round 1 "조건부 통과" 헤더가 Round 2 PASS 후에도 지연 반영되던 실제 사건(세션99 본건) 재발 방지
- 구현: `final_check.sh` 4.5 섹션 신설 — L7 `최종 업데이트` 헤더에 "조건부/Round 1/보류" + 섹션0 본문 "최종 판정" 이후 5줄 내 "**통과**/PASS/통과 (PASS)" 둘 다 매칭 시 `warn`
- 검증: 포지티브(정합) OK / 네거티브(헤더만 조건부로 재현) WARN 정상 감지 / smoke_fast 11/11 PASS
- 훅 등급: advisory (차단 없음, stderr 경고만)


**[완료] generate_agents_guide.sh hooks 파서 M3/M4 패턴 전환**
- 로그: `90_공통기준/토론모드/logs/debate_20260423_212854/round1_gpt.md`
- A 분류 자가판정 (버그 수정, 실행 흐름·판정 분기 불변). GPT 동의 — 3자 승격 불필요
- **변경 파일 1건**: `90_공통기준/업무관리/generate_agents_guide.sh` L7-38
  - `grep -oE "...\\.sh\"" ... | wc -l` 셸 손파싱 → `parse_helpers.py --op hooks_from_settings` (team+local union)
  - Windows \r 이슈 대비 `tr -d '\r '`. M3/M4 선례 재사용
- **GPT 조건부 통과 보강 3건 전부 반영**:
  - PY_CMD fallback (`doctor_lite.sh:10-11` 선례) — Windows/경량 환경 Python 부재 대응
  - 헤더 문구 `"settings.local.json 기준"` → `"settings.json+settings.local.json 기준"` (union 정합)
  - settings 둘 다 부재 시 `[WARN] settings files missing` stderr 1줄 (원인 은닉 방지)
- **증상 해소**:
  - `AGENTS_GUIDE.md` "0개 활성" → "31개 활성"
  - `final_check --fast` 3.5 섹션 WARN → `[OK] AGENTS_GUIDE hooks 개수 일치 (31개)`
- **회귀**: smoke_fast 11/11 ALL PASS
- **명시적 비변경**: README 계층별 훅 테이블 파싱(L47-62 별건 M5 후보), SETTINGS dead assignment 정리(별건)

---

## 세션98 (2026-04-23) — 시스템 전체 드리프트 2자 토론 + 실행

**[완료] GPT 시스템 평가 실물 대조 + Explore 3병렬 독립 스캔**
- GPT 8건 중 7건 사실, 1건(post_commit_notify 배치) 반만 사실로 확인
- Claude 독립 발견: 도메인 STATUS 5개 drift 12~23일(High), 고아 폴더 5개(Med), 정리대기_20260328(Med)
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260423_193314/`

**[완료] 2자 토론 Round 1 합의 (3자 승격 불필요)**
- 의제1 A안 채택: `DESIGN_PRINCIPLES.md:10` "정적 출력만" → "정적 + advisory 보조 허용" 문구 현실화
- 의제1 부가: parse_helpers M4 선행, M3 지연 불가 (GPT 조건 수용)
- 의제2 C2 채택: 신규 advisory 훅 `domain_status_sync.sh` 신설 (1 Problem ↔ 1 Hook)
- 의제3 수정 채택: URL echo 7건·숫자 echo 8건 제거 (포괄 통합 아님), dry-run 3건 통합

**[완료] 즉시 실행 4건**
- `smoke_fast.sh` 주석 "5~8건" → "11건" (실제 검사 수와 일치)
- `harness_gate.sh` 주석 "마지막 5000자" → "마지막 20000자" (실제 tail -c와 일치)
- `README.md` `post_commit_notify.sh` Notification 층 → 추적층(PostToolUse) 이동 + event 명시
- `DESIGN_PRINCIPLES.md` L10 A안 문구 수정

**[완료] parse_helpers M4 — `risk_profile_prompt.sh` 셸 파서 이관**
- 기존 셸 while + grep + sed 블록(L85-141) 제거 → `parse_helpers.py --op match_domain` 호출
- `parse_helpers.py`에 `match_domain_by_keywords()` 신규 함수 + CLI op 추가
- 회귀: smoke_fast 11/11 PASS, active_domain.req 정상 작성

**[완료] parse_helpers M3 — `final_check.sh` 4개 자체 파서 이관 (SSoT 종결)**
- `registered_hook_names` / `readme_active_hook_count` / `readme_active_hook_names` / `status_hook_count` 함수 내부를 parse_helpers CLI 호출로 대체
- Windows Python stdout \r 삽입 이슈 발견 → `tr -d '\r'` 추가
- DESIGN_PRINCIPLES 원칙 7 "Single Source of Truth" 실제 코드로 끝남

**[완료] C2 `domain_status_sync.sh` 신규 advisory 훅**
- 전역 TASKS 날짜 vs 도메인 STATUS.md 5개 날짜 비교 → 14일+ drift 감지 시 stderr 경고
- 실측: 05 조립비정산 17일·10 라인배치 23일 drift 감지 확인
- `session_start_restore.sh`에 호출 추가, fail-open / exit 0 강제
- 30일 실측 후 gate 승격 여부 재평가 (2026-05-23)

**[완료] permissions.local.json 정리 (63 → 27, 57% 감축)**
- URL echo 7건 제거 (`Bash(echo:*)` 팀 포괄 이미 존재 — 중복 제거)
- 숫자 echo 8건 제거 (대화방 ID 1회용 — 영구 허용 가치 없음)
- dry-run 3건 + 기타 incident_repair 호출 6건 → `Bash(python3 .claude/hooks/incident_repair.py:*)` 1건으로 통합
- 1회용 mkdir/rmdir/tmp py/worktree cleanup/chrome debug 다수 제거

**[완료] GPT 최종 판정 후속 마무리 (실행 가능 항목 전부)**
- GPT 지적: README smoke_fast "5~8건" 문구 잔존 → `.claude/hooks/README.md:149` "11건"으로 정정
- GPT 지적: 도메인 STATUS 5개 실물 drift 잔존 → 02/04/06/05/10 헤더에 세션98 전역 점검 stamp 추가 ("도메인 내용 변경 없음" 명시로 정직성 유지)
- `domain_status_sync.sh` 정규식 강화: 파일 내 모든 YYYY-MM-DD 중 최대값 선택으로 변경 (이전: 첫 매치만 → 헤더 포맷에 최신/구 날짜 혼재 시 오판). drift 0건 확인
- AGENTS_GUIDE.md 재생성 (generate_agents_guide.sh 실행, skills 20개 반영. hooks=0 버그는 스크립트 별건)
- `state/` 7일+ 마커 2건 정리 (debate_independent_review.ok / 구 세션 skill_read.ok)
- 고아 폴더 5개 유지 결정 기록 (사용자 지시, 드리프트 재분류 금지)
- **GPT 최종 판정: PASS** (세션98 닫음, 잔여 3건은 별건 의제로 분리)

**[완료] 98_아카이브 정리대기_20260328 분류 (Option C)**
- `_cache/` 6건 + `run_logs/` 16건 = 22건 삭제 (재생성 가능한 임시 캐시·로그, git tracked 아님)
- 나머지 71건 보존 + 폴더 rename: `98_아카이브/정리대기_20260328/` → `98_아카이브/구버전_20260328/` (30일 정리대기 규칙 벗어남, 참조 가치 유지)
- 보존 내용: 구버전_스킬(6) / 구버전_임률단가(13) / 구버전_조립비정산_스크립트(19) / 구버전_조립비정산_엑셀분석(30) / 보류판정_아카이브(2) / 보류파일목록_20260328.md(1)

---

## 이전 세션 (세션96 이하) — 아카이브

- 세션90~96 상세: `98_아카이브/session91_glimmering/TASKS_session90~96.md` (세션103 감량)
- 세션88 이하: `98_아카이브/session91_glimmering/TASKS_~session88.md`
