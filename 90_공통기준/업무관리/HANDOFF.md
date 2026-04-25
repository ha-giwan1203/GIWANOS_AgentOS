# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-25 KST — 세션109 SD9A01 숙련도평가서 자동화 (Phase 1~5 완료, 35 산출물) / 세션108 클로즈
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 세션109 (2026-04-25) — SD9A01 공정별·개인별 숙련도평가서 자동화

### 진행 상황
- 사용자 트리거: "SD9A01 라인 안건 진행하자" + ERP 표준공정관리 화면(SD9 OUTER #01, 11공정) 캡처
- 작업계획.md(10공정) → ERP 11공정으로 정정. 신규 SD9A01_003(릴브라켓 리벳팅) 1건, 명칭 변경 다수
- Plan 작성·승인 → auto-mode Phase 1~5 일괄 실행

### 산출물 (35개)
- `01_인사근태/숙련도평가/SD9A01_표준문서/SD9A01 작업표준서 통합_Rev16.xlsx` (17시트, 29 MB)
- `01_인사근태/숙련도평가/SD9A01_공정별 평가서/SD9A01_공정{001~011} 숙련도 평가서.xlsx` × 11
- `01_인사근태/숙련도평가/SD9A01_개인별 평가서/SD9A01 주간|야간/{이름} 숙련도평가서.xlsx` × 23

### 신규 스크립트 (3개)
- `생성스크립트/merge_sd9a01_workstandard.py` — Excel COM .xls→.xlsx + 시트 복사
- `생성스크립트/create_sd9a01_v1.py` — PROCESSES 자동 추출(통합본) + 양식 11 생성
- `생성스크립트/create_sd9a01_personal.py` — SD9M01→SD9A01 코드 매핑 + 23명 개인별

### 다음 AI 액션
1. **사용자 텍스트 검수**: 공정별 양식 11개의 평가사항(특히 GENERIC 보강된 항목)을 공정 실태와 비교 → PROCESSES 정정 시 `create_sd9a01_v1.py` 재실행으로 일괄 갱신
2. **인쇄 검수**: SD9A01_공정001 + 박태순 개인별 샘플 Excel 인쇄 미리보기 → 페이지 분할 정상 여부
3. **결정사항 정리**: 작업계획.md 결정사항 D(파일명 명명규칙), E(23명 확정), F(180706 시트 20 보존됨)

---

## 세션108 (2026-04-25) — GPT 정밀평가 검증 후 모드 전환

### 진행 상황
- 사용자 모드 전환: "실무 산출물 우선, 시스템 개선 중단". 마지막 한 사이클 — 검증 후 근본 드리프트만 최소 보정.
- GPT 정밀평가 리포트 L-1~L-7 / P-1~P-5 수령 → 실물 대조 검증

### 검증 결과
- **L-1 실증 (근본문제)**: `STATUS.md:34` "Chrome MCP 단일화. CDP 폐기" — 세션32 history가 현재 정책처럼 표기. 토론모드 CLAUDE.md(현 정책: CDP 단독)와 충돌 → **보정 완료**
- **L-2 실증 (근본문제)**: `hooks/README.md:29` "settings.local.json 배열 순서" — 라인 8 SSoT(settings.json)과 자체 모순 → **보정 완료**
- **L-3 드리프트 아님**: incident_session107_analysis.md(47건 스냅샷) vs TASKS(44건 누적) — 시점 차이. 보정 불요
- **L-5 PASS (사용자 추가 지시)**: list_active_hooks --count=32, README/AGENTS_GUIDE 모두 일치, 등록훅 실존성 PASS. 추가 조치 불요
- **L-6 명시 강화 완료 (사용자 추가 지시)**: hooks/README.md PreToolUse 섹션에 통합·삭제 금지 + 고정 순서 변경 금지 1줄 명시
- **L-4 권한 차단 (보류)**: 사용자 지시 있었으나 권한 시스템이 settings.local.json 편집을 2회 차단. 진행하려면 명시적 settings 편집 승인 필요
- **L-7 의도적 미해결**: 사용자 본인이 세션107에서 명시 취소
- 실측 incident: total 1141 / unresolved 102 (TASKS 표기 44건 + 이후 신규 58건, 정상 누적)

### 다음 AI 액션
- **시스템 개선 모드 중단**. 실무 산출물 작업으로 전환.
- 허용: 산출물 생성 / 작업 차단 오류 최소 수정 / TASKS·HANDOFF 필수 기록 / final_check 1건 단위 보정
- 금지: hook 추가, settings 구조 변경, 토론 자동 승격, incident 대량 정리, 문서 체계 재설계
- GPT 토론방에 모드 전환 공유는 사용자 지시 시에만 진행

---

## 세션107 (2026-04-25) — GPT 시스템 정합성 검토 + 3자 토론 L-4

### 진행 상황
- 사용자 트리거: "gpt토론방 내용 확인후 내 계획을 듣고 싶어" → GPT L-1~L-5 지적 5건 수령
- 독립 라벨 부여(실증됨/일반론/환경미스매치/메타순환/구현경로미정) 후 A 분류 즉시 반영
  - L-1 hook 32개 수동 표기 제거 (STATUS/README) — 커밋 e7a9afbb
  - L-2 SKILL.md frontmatter β안-C 예외 명시 — 커밋 e7a9afbb
  - L-3 SKILL.md 구 MCP 표기 → chrome-devtools-mcp 갱신 — 커밋 e7a9afbb
- L-4 navigate_gate.sh 보호자산 등록 = B 분류 → 3자 토론 자동 승격 (만장일치 pass_ratio=1.0) — 커밋 65efca24
  - 양측 추가 위험 통합: GPT(보호 착시) + Gemini(settings.json 우회 무력화)
  - 로그: `90_공통기준/토론모드/logs/debate_20260425_115300_3way/`
- L-5 incident 158건 분석: session_drift 27건 전부 final_check "STATUS<TASKS" 드리프트 → STATUS.md/HANDOFF.md 헤더 세션107 갱신으로 신규 발생 차단

### 클로즈 상태 (세션107 잔여 정리 후)
- **Push 완료**: e7a9afbb + 65efca24 + aac8a9bf + 후속 커밋 모두 origin/main 반영. `Bash(git push:*)` 권한은 `.claude/settings.json:15`에 영구 등록(팀 공용)되어 있음 — settings.local.json 중복 entry 제거
- **L-5 incident 처리 완료**: 의제 A~D 100건 일괄 해소 + 잔존 47→44건 추가 정리 → TASKS.md 세션107 항목으로 처리. 잔존 44건은 정당한 차단 기록(보존)
- **B-2 완료**: hook_incident hook/type 필드 누락 추적 강화 (record_incident.py --hook required + hook_common.sh 빈 entry WARN)
- **D-2 폐기**: navigate_gate trip은 정상 안전장치 동작, 신규 발생 자체가 정책 위반 아님

### 잔여 정리 (세션107 말미)
- `.claude/settings.local.json` 한글 mojibake 12+/9- 복구 + daily-routine 절대경로 2건 보존 (`Bash(git push:*)`는 settings.json 영구 등록과 중복으로 제거)
- `.gitignore`에 `*.bak_session107_pre_port9223` 추가 → 백업파일 9개 untracked 해소
- HANDOFF "미해결" 섹션 사실관계 보정 (push 완료/L-5 처리 완료 반영)

### 다음 AI 액션 (세션108)
1. **[최우선]** 2026-04-26 (일) 22:00 `D0_SP3M3_Verify_Sunday` 임시 모의 구동 결과 확인 (parse-only) — `verify_20260426_220000.log` LastResult=0 + selectList listLen=21 확인. 통과 시 task 삭제 (`schtasks /Delete /TN "D0_SP3M3_Verify_Sunday" /F`). 실패 시 월요일 07:10 트리거 전 즉시 대응
2. **[최우선]** 2026-04-27 (월) 07:10 `D0_SP3M3_Morning` 자동 실행 결과 확인 — LastResult=0 + `morning_20260427.log` 정상 생성. 일요일 검증 통과 + #btnExcelUpload 30s 확장(3d516e22) 효과 종합 검증
2. session_kernel.md stale 갱신 메커니즘 점검 (현재 fallback 동작 정상)
3. 신규 의제 발굴 또는 사용자 트리거 대기

### D0 자동화 신규 자산 (세션107 말미)
- `--parse-only` 옵션: Phase 3 selectList까지만(DB 저장 안 함). 검증 전용
- `_wait_d0_popup_frame()` 헬퍼: iframe URL 늦게 set되는 경합 대응 (frame URL + DOM querySelector 이중 폴링, 25s)
- `run_morning_verify.bat`: parse-only 호출 wrapper (향후 동일 검증 재사용)

---

## 세션106 (2026-04-25 아침) — D0_SP3M3_Morning 스케줄러 LastResult=3 근본 해결

### 진행 상황
- 사용자 질의: "7시 10분 스케줄러 작동하나?" → Windows 작업 스케줄러 점검
- `D0_SP3M3_Morning` (월~토 07:10) 등록 활성, 오늘(토) 07:10 트리거됨, **LastResult=3 실패**
- LOGFILE 미생성 → batch 자체 시작 실패 의심 → 직접 실행으로 인코딩 깨짐 확인
- 수정 후 재실행: batch 정상 → python 진입 → ERP 접속에서 `ERR_BLOCKED_BY_CLIENT` 별건 확인

### 다음 액션 (D0 스케줄러 완전 정상화)
1. CDP Chrome 프로필 (`C:\temp\chrome-cdp`) 확장 목록 점검 (광고 차단/보안 확장 의심)
2. D0 자동화가 사용하는 Chrome 프로필 식별 — `run.py`에서 connect over CDP인지 launch인지 확인
3. 토론모드 CDP Chrome (포트 9222)과 D0 자동화 프로필 분리 가능성 검토
4. 월요일 07:10 실 트리거 전까지 수동 검증 1회 더 권장

### 다음 트리거 일정
- D0_SP3M3_Morning 다음 실행: **2026-04-27 (월) 07:10:00** (Windows 작업 스케줄러)
- 그 전까지 ERR_BLOCKED 미해결이면 다시 LastResult=1 발생 예상

---

## 세션105 (2026-04-24 저녁) — 시스템 개선 3자 토론 + 탭 전환 근본 해결

### 진행 상황
- 3자 토론 Round 1 GPT/Gemini 답변 수집 완료 (`90_공통기준/토론모드/logs/debate_20260424_195811_3way/`)
- Q1 불일치 (GPT=C vs Gemini=B) / Q2·Q3 합의 (A안)
- 탭 전환 근본 해결 완료 — Round 2 재개 가능

### 탭 전환 해결 — 완료
- 원인 확정: Claude in Chrome MCP가 CDP `Target.activateTarget` / `Page.bringToFront` 차단
- 해결책: `chrome-devtools-mcp` (Google 공식) 병행 설치 — `list_pages` / `select_page` 사용
- Step 1 ✅ `chrome-devtools-mcp` user scope 등록
- Step 2 ✅ Chrome 포트 9222 LISTENING (별도 프로필 `C:\temp\chrome-cdp`)
- Step 3 ✅ chrome-devtools-mcp ↔ 포트 9222 연결 확인 (본 세션 ToolSearch로 로드됨)
- ChatGPT·Gemini 양측 CDP Chrome 로그인 완료

### 중요 제약 — Chrome M136+ 보안
- 기본 프로필에서 `--remote-debugging-port` 플래그 무시됨 (세션 쿠키 탈취 방어)
- 반드시 별도 `--user-data-dir` 필요 → 본 저장소는 `C:\temp\chrome-cdp` 사용
- 향후 토론모드는 해당 프로필의 CDP Chrome에서 진행

### Round 2 합의 성립 (2026-04-24 22:10 KST)
- Q1 = 기타안 만장일치 (pass_ratio 4/4)
- Round 2 GPT: 기타안 (B 실측 선행 + C 임계값 폐기)
- Round 2 Gemini: 기타안 동조 (TASKS 조건 tightening 1건)
- Claude 종합: 기타안 + Gemini tightening 통합 → 양측 동의
- 로그: `round2_gpt.md`, `round2_gemini.md`, `round2_claude_synthesis.md`, `round2_cross_verify.md`

### Q5 Claude 독자 답안 선행 강제 완료 (세션105 2026-04-25, 사용자 지시 예외 D안)
- SKILL.md Step 3-W 6-0 단계 신설: `round{N}_claude.md` 선행 작성 필수
- debate_independent_gate.sh 매처 확장 (chrome-devtools-mcp__evaluate_script) + 셀렉터 확장 (ql-editor 병행)
- 회귀 테스트 5건 PASS
- **다음 세션 첫 토론 send 전 필수**: `touch .claude/state/debate_independent_review.ok` (첫 Round 1 전송 허용용 마커)
- 사유: Round 2 Q1·Q4에서 Claude 독자 답안 선행 없이 양측 축약만 → 3-way 기여 실증 불가 (사용자 지적, 2026-04-25)

### Q4 navigate_gate 재검토 완료 (세션105 말미, 3자 토론 pass_ratio 4/4)
- 로그: `90_공통기준/토론모드/logs/debate_20260424_230014_3way/`
- A안 만장일치 (최소보강 — navigate_page/new_page 매처 확장, select_page 제외)
- settings.json matcher 2개 추가 + navigate_gate.sh URL 파싱 확장
- 회귀 테스트 5건 PASS (네거티브/포지티브/비대상/new_page/비chatgpt URL)
- 효과성 평가: 7일간 send_block 0~2건 정상 / 부당 오탐 3건 이상 시 재상정

### Q3 auto-fix 1차 분류 완료 (세션105 말미)
- 보고서: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/q3_auto_fix_classification.md`
- 미해결 80건 → 7개 카테고리
- **Q1 재점화 조건 4** (auto_commit_state 상위 3개 진입): 수치 충족, 단 Q1 기타안 해석과 일치하여 재상정 불필요
- 다음 Q4 후보: "navigate_gate 감지 기준 재검토" (11건)
- Category D (session_drift 10건) `/finish` 자동 해소 시도 가능

### Q1 기타안 후속 실행 완료 (세션105 말미)
1. ✅ audit — 최근 14일 15건, 모두 2026-04-24 하루 집중, classification 단일(`completion_before_state_sync`). 격상 불필요 결론
   - 보고서: `90_공통기준/토론모드/logs/debate_20260424_195811_3way/audit_auto_commit_state.md`
2. ✅ advisory 강화 — `auto_commit_state.sh` 차단 메시지에 미동기화 AUTO 파일 목록 + 최근 60분 중복 건수 + 재점화 조건 1 근접 경고 추가 (실행 흐름 변경 없음)
3. ✅ TASKS.md에 재점화 4조건 공식 등록 (세션105 Q1 최종 정책 섹션)

### 4개 스킬 마이그레이션 (세션105 후반)
- `.claude/commands/gpt-send.md`, `gpt-read.md`, `gemini-send.md`, `gemini-read.md` 전면 재작성
- `90_공통기준/토론모드/CLAUDE.md` 탭 throttling 대응 + Chrome MCP 금지 범위 갱신
- 상태 파일 `gpt_tab_id`·`gemini_tab_id` 의미 변경: tabId 문자열 → pageId 정수
- 사용자 지시 예외(D안 선례) 적용 — B분류 구조변경이지만 사용자 "둘다" 명시 지시

### Round 2 실운영 중 추가 보강 (세션105 후반, Round 2 직후)
- **Chrome CDP launch 플래그 보강**: `--remote-debugging-address=127.0.0.1` 필수 명기 (IPv6 기본 바인딩 회피)
- **Chrome taskkill 주의**: 강제 종료 시 쿠키 DB 미플러시 → 로그인 소실. 창 닫기 권장
- **`gemini-send.md` Step 1-B-1 추가**: Gemini Gem 채팅방 진입 시 모델 설정이 고정되지 않음 → 전송 전 수동 확인/선택 단계 필수. `take_snapshot` + `click(uid)` fallback 명시

---

---

## 0. 다음 세션 시작 체크 (우선순위 1 — SD9A01 숙련도 평가서)

### 재개점
- 작업 계획서: [`01_인사근태/숙련도평가/SD9A01_작업계획.md`](../../01_인사근태/숙련도평가/SD9A01_작업계획.md)
- SP3M3 완료 (세션102, 13명 × 평균5공정 = 62시트 생성)
- SD9A01은 24명 × 6공정 = 약 144시트 예상 (약 2.3배 규모)

### 즉시 확인할 것
1. SD9A01 작업표준서 통합 방식 사용자 결정 (A=최신단독/B=자동병합/C=수기)
2. SD9M01 라인코드와 SD9A01 차이 확인 (표준문서=SD9A01 / 개인파일=SD9M01)

### 재사용 자산 (SP3M3 구현)
- `생성스크립트/create_sp3m3_v4.py` → SD9A01 베이스
- `생성스크립트/create_sp3m3_personal_v2.py` → SD9A01 personal 베이스
- 샘플: `공정 평가서표준_SP3M3_샘플.xlsx` (공용)

### SP3M3 구현에서 확정된 기법 (SD9A01도 동일 적용)
- 한 작업자 = 한 파일, 수행공정별 시트 (주공정 맨 앞)
- 샘플 복사 후 `wb.copy_worksheet()`로 시트 복제 (수식 100% 보존)
- 날짜는 'YYYY-MM-DD' 문자열 (datetime 객체 주입 금지)
- AC열 점수 분배: `random.Random(hash(작업자_공정))` 기반 + 0점 없이 base+1 보너스
- Z3 셀: 주공정/전환공정 라벨
- 업체=대원테크, 라인=SD9M01(또는 SD9A01) 명시

---

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260423_20260424.md`
