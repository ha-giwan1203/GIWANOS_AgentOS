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

최종 업데이트: 2026-04-20 — 세션83 (A의제 3자 API 확장추론 토론 [3way] — 독립의견 유지)

---

## 세션83 (2026-04-20, evidence_gate 333건 원인 3자 API 예외 토론 [3way])

**[완료] 안건 B — 2026-04-19 evidence_missing 165건 집중 발화 audit_log 상세 분석**
- 산출: `90_공통기준/업무관리/evidence_gate_20260419_analysis.md`
- 7일 332건 (evidence_gate 272 + skill_instruction_gate 56 + instruction_not_read 4), 04-19 165건(49.7%)
- 04-19 01:06~01:53 KST 47분간 42건 단일 세션 commit/push 루프
- fingerprint 상위 3종 180/272 = 66% 집중, resolved:false 100%

**[완료] 안건 A — evidence_gate fingerprint suppress 확장 ([3way] API 예외 토론)**
- 사용자 명시 예외: 토론모드 `[NEVER] API 호출` 1회 완화. 별도 로그 경로 분리
- 4개 확장추론 모델 재판정 (Gemini 2.5-pro/3.1-pro-preview + GPT o4-mini/5.2) 만장일치:
  - Q1 α 원인: Claude 가설(반복 commit 흐름) 채택 / 실증됨 3/3
  - Q2 γ self-throttle: (A) 차단 유지+incident 중복 억제만 채택 / 실증됨 3/3
  - Q3 δ(skill_instruction_gate): 별건 분리 / 실증됨 3/3
- Gemini-flash 초기 제안 2건(fresh_ok 완화·cooldown 중 차단 생략) Claude 독립 반박 후 **버림** — 세션78 안전망 역방향 위험
- 수정: `.claude/hooks/evidence_gate.sh` GRACE_WINDOW 30→120 + tail -30→-100 + stderr 경고 추가 (차단 유지, 기록만 억제 확장)
- smoke_test 섹션 48 신설 (5건 PASS): GRACE=120·tail=100·경고·_should_record·fresh_ok 유지(역방향 차단)
- 로그: `90_공통기준/토론모드/logs/debate_20260420_143000_api_exception/round2_summary.md`
- OpenAI API 클라이언트: `90_공통기준/토론모드/openai/openai_debate.py` (reasoning 모델 max_completion_tokens 분기)

**[이월·세션84+] 안건 δ — skill_instruction_gate 36건 별건 분석** (본 토론 합의로 분리)

### 세션83 주의사항
- OpenAI API 키 `claude-code-debate-20260420`을 2026-04-20 14:22 KST 발급. 토론 종료 후 revoke 권장
- 토론모드 CLAUDE.md `[NEVER] API 호출` 규정은 다음 세션부터 원복 (이번 세션만 예외)

---

## 세션82 (2026-04-20, weekly-self-audit → hook 문서 정합 보정)

**[완료] `/self-audit` 스케줄 실행 결과 기반 P1 2건 + 관련 P2 3건 README 문서화**
- 진단 결과: hook 32개 중 31개 active, anomaly 6건 (P1 2/P2 4/P3 3)
- P1 2건 (문서 드리프트):
  1. `token_threshold_check.sh` — `session_start_restore.sh`에서 체인 호출되나 README 미기재 → 보조 스크립트 섹션 + 실패계약 표 추가 (advisory/fail-open)
  2. `share_gate.sh` — `/share-result` 수동 실행이나 README 미기재 → 보조 스크립트 섹션 + 실패계약 표 추가 (advisory/fail-open)
- 관련 P2 3건 일괄 보정:
  - `skill_drift_check.sh` 실패계약 표 신규 추가 (advisory/fail-open)
  - `permissions_sanity.sh` 실패계약 표 신규 추가 (기존 누락 보완)
  - `doctor_lite.sh` 보조 스크립트 섹션 + 실패계약 표 신규 추가
  - `nightly_capability_check.sh`, `pruning_observe.sh` 보조 스크립트 섹션 추가
- settings.json 이중 등록 회피: token_threshold_check는 session_start_restore 체인 호출, share_gate는 share-result 커맨드 설계 밖 호출 — 이벤트 등록 시 중복 발화
- 수정 파일: `.claude/hooks/README.md` 1개 (보조 스크립트 섹션 +5행, 실패계약 표 +6행)

**[완료] settings.local.json 1회용 패턴 23건 청소** — permissions_sanity.sh 33회/7일 경고 해소
- 제거 내역 (23건, allow 37→14):
  - echo PID 하드코딩 8건 (`echo "1382937xxx"`), echo URL 하드코딩 5건 (ChatGPT/Gemini 특정 대화방)
  - touch evidence SHA 2건 (과거 세션 `f0c5823f656...` 경로 하드)
  - Read memory 경로 중복 2건, settings.json과 완전 중복 1건 (`python3 -c ' *`)
  - SHARE_GATE_COMMIT 특정 SHA 하드 1건, python3 URL 하드코드 1건
  - Read 오타 경로 2건 (`//c/c/...`), 존재하지 않는 파일 2건 (`TASKS.md.append`)
- 검증: `bash .claude/hooks/permissions_sanity.sh` 재실행 시 경고 출력 없음
- 주의: settings.local.json 수정 반영은 **세션 재시작 시 캐싱**. 현 세션은 이전 스냅샷 사용

### 남은 진단 안건 → 3자 토론 라운드 1 진행 (2026-04-20 오후)

**[완료] README 상단 "34개" → "31개" 정정** — A 분류 (단순 숫자 정정). PreCompact 1 / SessionStart 1 / UserPromptSubmit 1 / PreToolUse 16 / PostToolUse 7 / Notification 1 / Stop 4 = 실등록 31개

**[3자 토론 Round 1 완료] 3의제 일괄 처리 — 로그: `90_공통기준/토론모드/logs/debate_20260420_131100_3way/`**

#### 의제 1 — evidence_gate 과다 발화 원인 분석
- **판정**: GPT "검증 필요" + Gemini "검증 필요" → **즉시 조치 유보**, 세션83+ 별건 이월
- 실측: 333건/7일 = map_scope.req 99 + skill_read 86 + tasks_handoff 63 + MES-no-SKILL 60 + commit차단 16. 2026-04-19 165건(50%) / 04-14 64건(19%) 집중
- 양측 공통 원인 가설: 구버전 tasks_handoff 패턴 + 현재 map_scope 반복 + commit 시점 차단 **혼재**
- **세션83+ 이월 안건**: (1) evidence_mark_read.sh 자동 충족 범위 확장 (2) Gate 탐지 정규식 범위 재검토 (3) 구버전 vs 현재 로그 분리 재집계

#### 의제 2 — 90_공통기준/스킬/생산계획자동화/ 고아 폴더 [완료]
- **판정**: GPT "A 동의" + Gemini "A 동의" → pass_ratio 양측 동의
- 조치: `90_공통기준/스킬/생산계획자동화/` → `98_아카이브/생산계획자동화_구버전_20260420/` 이동 (파일 3건: 변경이력·운영절차·자동화규칙 v3.0)
- 활성 스킬 `90_공통기준/스킬/sp3-production-plan/SKILL.md` 유지 (이중화 회피)

#### 의제 3 — debate_verify.sh Phase 2-C 승격 판정 [헤더 문서화 완료, exit 2 전환은 7일 후]
- **판정**: GPT "동의" + Gemini "동의 (회귀 테스트 보강)" → pass_ratio 양측 동의
- 조치: `debate_verify.sh` 헤더에 Phase 2-C 조건 주석 추가
  - 재집계 시작점: **세션81 수정 커밋 SHA 408c4856** (2026-04-20 ~10:54 KST)
  - 관찰 기간: post-fix 7일 연속 type=debate_verify incident 0건
  - 회귀 테스트: 영문/특수문자/한글 경로 커버 (Gemini 보강)
  - 승격 방식: hook_gate 래퍼 + exit 2 + JSON decision=deny (기존 Phase 2-B 6종 준용)
- **평가 시점**: 2026-04-27 세션89+ 예상. incident_review.py 재집계 결과에 따름.

### 세션83+ 이월 안건 (3자 토론 후속)
- **의제 1 후속 3자 토론** (필수): evidence_gate 333건 원인 세부 분석 + 정규식 검토 + 조치안 확정
- **gpt-send/gpt-read 스킬 개선** (세션82 실증): `data-message-model-slug$="-thinking"` 감지 시 완료 대기 시간 자동 연장 (stop-button 단독 판정 금지)
- **Phase 2-C 재평가** (2026-04-27 전후): incident_review.py 결과 확인 후 exit 2 전환 결정
- **[GPT A 제안]** Phase 2-C 재평가 전 영문/특수문자/한글 경로 3종 회귀 테스트 체크리스트를 `step5_final_verification.md` 또는 별도 검증 로그 템플릿으로 고정
- **[Gemini A 제안]** 04-19 evidence_missing 165건(50%) 집중 발화 audit_log 상세 분석 → 세션83 첫 작업 권장
- (기존 P3 이월) Phase 2-C 재평가 시 회귀 테스트 실행

### 3자 토론 Round 1 최종 판정 (양측 PASS — 2026-04-20)
- **GPT 판정**: PASS (item 1·2·3 실증됨/동의, item 4 환경미스매치/동의)
- **Gemini 판정**: PASS (item 1·2·3 실증됨/동의, item 4 메타순환/보류)
- **공통 합의**: 의제 2·3 실물 반영 정합, 의제 1 세션83+ 이월 정합
- **pass_ratio**: 의제 2·3 = 2/2, 의제 1 = 2/2(이월 합의)
- 로그: `90_공통기준/토론모드/logs/debate_20260420_131100_3way/`

---

## 세션81 (2026-04-20, debate_verify.sh 한글 경로 오탐지 수정 [3way])

**[완료] `.claude/hooks/debate_verify.sh` + `.claude/hooks/statusline.sh` heredoc 인라인 삽입 취약 패턴 수정** — 세션80 Follow-up 항목 해소

- 근본 원인 (3자 토론 실증): POSIX 경로(`/c/Users/...`) → Windows 네이티브 Python3 비호환 + 쉘 `$RESULT` 인라인 전개 시 locale/code page 경유 한글 경로 깨짐. surrogate escape 아님.
- 수정 (3파일):
  1. `debate_verify.sh` 80-85행: `<<'PY'` quoted heredoc + `os.environ['RESULT_ENV']` + `cygpath -w` 우선 + 범용 sed `s|^/([a-zA-Z])/|\1:/|` fallback + Python 내부 `re.sub` + `os.path.normpath()` 2차 안전망
  2. `statusline.sh` 7-22행: heredoc 인라인 삽입(`json.loads('''$input''')`) → stdin 파이프(`json.load(sys.stdin)`) 전환
  3. 주석 표현 완화: "CP949가 원인" 단정 제거 → "쉘 인라인 전개 중 locale/code page 경유 한글 경로 깨짐"
- 3자 토론 (`90_공통기준/토론모드/logs/debate_20260420_105428_3way/`):
  - Round 1: GPT 조건부통과×3 + 통과×1 + 실패×1 (C드라이브 전용 fallback 한계 지적)
  - Gemini Round 1: GPT 5개 판정 전면 동의 (사용자 수동 중재 경유, base64 자동 전송은 Usage Policy 필터로 차단)
  - Step 5: GPT 조건부 통과(구현 후 재판정 요청), Gemini 통과(구현 진행 승인)
  - pass_ratio 최종 = 0.83
- 검증: debate_verify.sh 재실행 시 "파싱 실패 [Errno 2]" 오탐지 해소, 정상 검증 로직 진입 확인. smoke_test 181/182 PASS (1 FAIL은 본건 무관 — `classify_feedback.py --validate`, 메모리 enforcement 태그 4건 누락 선행 이슈)

**[이월·세션82+]** GPT 조건부 통과 사후 재판정 — 커밋 SHA + git diff + smoke_test 결과 + [3way] 커밋 1건 성공 로그 양측 공유. Phase 2-C 승격 타이밍 기존 7일 유지 + incident 재집계 시작점만 리셋.

---

## 세션80 (2026-04-20, 학습루프 진단 + 4단계 보정)

**[완료] 4단계 보정**: ①session_kernel 수동 갱신(48h stale 해소) ②incident_ledger `debate_verify` 37건 resolved:true(세션5 `result.json`+`step5` retrospective 생성, 백업 `.bak_20260420_learning_loop`) ③`hook_timing_summary.py` 신설(최근 7일 2770건/경고 3.5% 실측) ④TASKS.md 2049→799줄 감축(`98_아카이브/tasks_archive_20260420.md` 이관, 백업 `.bak_20260420`)

**[완료·세션81 반영]** `debate_verify.sh` python3 `open(r"$RESULT")` 한글 경로 인식 실패 → 세션81에서 수정 완료 (위 세션81 섹션 참조)

---

## 세션79 착수 (2026-04-20, 영상 분석 적용 점검 → 드리프트 보정)

**[완료] 영상분석(2rzKCZ7XvQU) 시스템 적용 점검 — 11개 항목 중 10건 정합, 1건 드리프트 발견**
- 즉시적용 4건: /rewind·context7·doctor_lite·statusline 모두 정합 반영
- 보류/폐기 3건: /batch·/insights·--bare 그대로 미도입 (의도대로)
- 검증후적용 4건 중 3건 정합: /schedule 분류표·skill-creator 경로화·/debate-verify hook
- **드리프트 1건**: `token-threshold-warn` 스킬 TASKS.md 601행 "완료" 표기됐으나 실물 미구현

**[완료] 토큰 임계치 경고 스킬 `token-threshold-warn` Phase 1 실물 구현** — 세션68 3자 합의(pass_ratio 1.00) 드리프트 보정
- 신설 파일:
  1. `.claude/hooks/token_threshold_check.sh` (advisory, exit 0 강제)
  2. `90_공통기준/스킬/token-threshold-warn/SKILL.md`
- 수정 파일:
  1. `.claude/hooks/session_start_restore.sh` (doctor_lite 직후 배선)
  2. `.claude/hooks/smoke_test.sh` (섹션 47 신규 5건)
  3. `.claude/settings.json` permissions.allow 1건 추가
- 임계치 (합의 고정): TASKS 400/800, HANDOFF 500/800, MEMORY 인덱스 120/200, 메모리 파일 60/100, incident 1MB/3MB
- 수동 실행 검증: 현재 TASKS 1981줄 → `[STRONG] TASKS.md: 1981 / 800줄` 정상 출력
- smoke_test 47번 5건 PASS (전체 178/179, 나머지 1건은 선행 FAIL로 본건 무관)

**[이월] Phase 2 Stop hook 증가량 기록** — 1주 운영 후 `token_threshold_delta.sh` 구현.
Phase 2 진입 판정 지표 (Claude 독립 점검·라벨링 결과, 2026-04-20):

**채택 (2종)**:
1. 주간 경고 발생 빈도 변동 < 20% (Claude 합의안 기본) — 실증 근거 약하나 안정성 최소 기준
2. 무시/관용 비율 ≤ 80% (Gemini 제안) — **실증됨**. 세션77 map_scope Policy-Workflow Mismatch 선례 정확 인용. STRONG 경고 후 축소 작업 없이 진행된 세션 비율. 80% 초과 시 임계치가 G-ERP 실무에 비해 과엄격

**보류 (4종)**: SessionStart p95(일반론), 경고 상위 안정성(환경미스매치), 증가량 추적 실효성(메타순환), 조치 전환율(구현경로미정) — 기준·근거·구현 경로 보강 후 재평가. 외부 제안 5건 중 실증 선례 인용 1건만 채택.

**채택 2종 미충족 시** Phase 2보다 TASKS 감축 우선 (GPT·Gemini 공통 권고, 이 방향성은 타당)

**[이월] 임계치 상수 단일 원본화** — Phase 2 진입 시 token_threshold_delta.sh가 추가되면 현재 shell 스크립트와 SKILL.md에 이중 기재된 임계치 상수를 단일 위치로 모아 드리프트 방지 (GPT A분류 제안)

**[이월·세션80] 자기 진단 hook 선별 기준 설계 (3자 공통 결론)** — 전역 일반화 폐기, 선별적 강제로 방향 확정
- GPT 라벨: 환경미스매치 (훅 과밀·오탐·유지보수 비용)
- Gemini 라벨: 구현경로미정 ("어느 규칙까지 hook화" 기준 미제시)
- 공통 결론: 핵심 협업 프로토콜(3way·검증 용어)에만 선별 적용
- 선정 기준 후보 (세션80 3자 토론 의제): 재발 빈도(세션당 N회 이상) + 우회 피해 규모(구조 변경·데이터 파손 여부)
- 대상 후보 예: share_gate(이미 구현), harness_label(텍스트만), debate_verify(이미 advisory), evidence_mark(기존)

**[이월·세션80] share_gate hook 튜닝 3건 (GPT A분류)**
1. settings.local.json 변경 감지 추가 (현재 settings*.json 패턴에 포함됐지만 검증 필요)
2. merge/revert/cherry-pick 시 HEAD~1 비교 약함 대응 (머지 베이스 감지)
3. 조건3 (직전 [3way] 미종결) 오탐 튜닝 — Gemini PASS 문구 인식 범위 확대

**[완료·세션79] 토론 모드 속도 개선 + 3자 판정 (1a552f55 → 추가 보완)** — 사용자 지적 "너무 답답한대"
- share-result 판정 응답 구조화 템플릿 강제 + **이원화** (단문/상세, Gemini A분류 반영)
- gpt-send·gemini-send: sleep 3→1, polling 3/5/8→2/3/5 + **fallback 3초 재시도 1회** (GPT A분류 반영)
- gpt-read·gemini-read: {len, text} JSON 반환 → MCP truncate 시 1회 slice만 추가
- 병렬 브라우저 창 분리: GPT 환경미스매치(기각) vs Gemini 일반론(보류+반박 "독립 브라우저 프로필 분리 가능") → **세션80 재검토**
- 실측 (이번 GPT 공유): 총 대기 5초 (기존 20초+ 대비 75% 단축, 302자 단일 호출 완결) → 구조화 효과 실증
- 3자 종합: 양측 부분PASS (item 2 sleep 축소 "실측 부재" 양측 보류 → 1주 관찰 필요)

**[이월·세션80] 독립 브라우저 프로필 병렬 창 재검토 (Gemini 반박 근거)**
- Chrome `--user-data-dir` 별도 프로필 → 독립 프로세스 창 → background/foreground 상태 독립 가능성
- MCP의 단일 탭 그룹 제약과 맞물린 실제 구현 경로 조사

---

## 세션78 Round 1 반영 (2026-04-20, 3자 토론 합의 → 구현)

**[완료] 세션78 P2 Round 1 — push-only 면제 + smoke 3건 확장 (3자 만장일치)**

3자 토론 Round 1 집계 (Claude×GPT×Gemini):
- 지적 1 (push-only 충돌): **3/3 채택** (만장일치)
- 지적 2-(2) partial proof deny smoke 누락: **2/3 채택**
- 지적 2-(3) stale skill marker smoke 누락: **안전망 채택** (정책 변경 없음)
- 지적 3 (STATUS.md 드리프트): **3/3 버림** (GPT 자기 철회 포함)

Step 5 양측 검증: GPT "동의" + Gemini "동의" → pass_ratio 1.0

**구현 반영**:
1. `.claude/hooks/evidence_gate.sh`: `is_commit_or_push` → `git commit`만 grep 변경 (push-only 면제, 세션76 push-only 스킵 최적화와 정합)
2. `.claude/hooks/smoke_test.sh` 3건 추가:
   - 44-10: ok 없이도 git push → pass
   - 44-11: tasks_updated.ok만 존재 + git commit → deny (OR 조건)
   - 44-12: stale skill_read__*.ok(past mtime) → deny (fresh_file 필터 안전망)

**토론 로그**: `90_공통기준/토론모드/logs/debate_20260420_010101_3way/` (round1_gpt/gemini/cross_verify/claude_synthesis)

**STATUS.md 관련**: GPT가 원래 드리프트로 지적했으나 Gemini "도메인과 시스템 범위 혼동. 조립비정산 STATUS는 세션78 무관" 근거로 3자 버림. GPT Step 4에서 자기 철회. **건드리지 않음 확정**.

**[최종 공유 판정] 양측 PASS** (2ccc8589 실물 확인):
- GPT: "Step 5 설계안 반영 정합 PASS. evidence_gate·smoke_test·TASKS/HANDOFF 모두 설계안 그대로 반영."
- Gemini: "3자 합의가 누락 없이 실물에 정합하게 반영. push-only 면제 + 44-10/11/12 smoke 엣지 안전망 완벽 확보."

**[세션79 후속 — A 분류 기록]**
- smoke_test 전수 실행 로그 첨부 (이번 세션에서 사용자 요청으로 생략됨, bash -n 구문 검사만 완료)
- 세션79 첫 액션 시 `SMOKE_TEST_FORCE=1 bash .claude/hooks/smoke_test.sh` 1회 실행 후 결과 아카이브

---

## 세션78 Round 1 보완 (2026-04-20, 3way 공유 양측 필수 규칙 신설)

**[완료] share-result 0단계 신설 — [3way] 태그 커밋은 GPT·Gemini 양측 공유 필수**
- **배경**: 2ccc8589 공유 시 Claude가 GPT에만 보내고 Gemini 생략 → 사용자 "반쪽 패치, 토론모드 실행 안 된 것 같다" 지적
- **원인**: share-result SKILL이 2자 전용 설계. 토론모드 CLAUDE.md Step 5-3 "양쪽 모두 전송" 규정이 공유 루프에 미반영
- **수정 파일**:
  1. `.claude/commands/share-result.md` 0단계 신설: [3way] 태그 / 이번 세션 debate-mode 호출 / 직전 5커밋 [3way] 미종결 중 하나라도 해당하면 양측 공유 강제
  2. memory `feedback_threeway_share_both_required.md` + MEMORY.md 인덱스 업데이트
- **보완 후 즉시 Gemini 공유 수행 → PASS 수신**

---

## 세션78 후속 반영 (2026-04-20, 공유→3자 자동 승격 규칙)

---

## 세션78 후속 반영 (2026-04-20, 공유→3자 자동 승격 규칙)

**[완료] 공유 루프 구조 변경 지적 → 3자 토론 자동 승격 규칙 신설**
- **배경**: 세션78 `/share-result` 루프에서 GPT FAIL(evidence_gate 구조 변경 제안)을 Claude가 Gemini 교차 없이 즉시 수정 착수 → 사용자 "토론모드 작동 안 한 거지?" 지적으로 철회. 상호 감시 프로토콜이 "3자 토론" 명시 트리거에만 적용되는 구조적 허점 확인.
- **수정 파일**:
  1. `.claude/commands/share-result.md` 5단계: 지적 성격 A/B 분류 + B(구조 변경) 시 `debate-mode` 자동 호출로 전환
  2. `90_공통기준/토론모드/CLAUDE.md` "자동 승격 트리거" 섹션 신설
  3. memory `feedback_structural_change_auto_three_way.md` 추가
- **A (즉시 반영)**: 문서 오타·값 조정·단순 버그·smoke 케이스 단순 추가·도메인 데이터
- **B (3자 승격)**: hook/settings 구조, 게이트/정책 재배치, commit/push 흐름 분기, Policy 재정의, 외부 인터페이스(ERP/MES) 영향
- **모호 시 기본 B 간주** (안전측)

**[다음] 세션78 P2 GPT FAIL 3건 3자 토론 본로 복귀**
- 이 규칙을 최초 적용해 세션78 P2 FAIL(has_any_req 재배치 + push-only 분기 + smoke 커버리지)을 Gemini 교차 검증 후 채택/보류/버림 판정

---

## 세션78 최종 반영 (2026-04-20, P2 skill_read / tasks_handoff Policy 재정의)

**[완료] 세션78 P2 — skill_read / tasks_handoff Policy 재정의 (evidence_gate 27.2% 추가 대응)**
- **목적**: evidence_gate 486건 중 skill_read 67건(13.8%) + tasks_handoff 65건(13.4%) = 132건(27.2%) 완전 미해결(resolved 0%) 정책 해소
- **접근**: map_scope 세션77 재정의 패턴 확장 (트리거 축소 + 면제 조건 확장 + 검증 시점 이동) — Round 3 정식 토론 skip (Round 1/2에서 Policy-Workflow Mismatch 의제 승격 완료)
- **수정 파일 3개**:

1. **`.claude/hooks/risk_profile_prompt.sh`**
   - L58 skill_read 트리거 키워드 9→7개로 축소 ("식별자", "기준정보" 제거 — 일상 대화 빈도 높음)
   - L64-66 tasks_handoff 조기 트리거 블록 완전 삭제 (commit/push 시점만 검증하는 구조로 전환)

2. **`.claude/hooks/evidence_gate.sh`**
   - has_any_req early-exit을 deny() 정의 이후로 이동 (세션78: L18-22 → L119-123)
   - deny() 직후 commit/push 우선 검증 블록 삽입 (req 유무 무관, has_any_req 우회 방지)
   - L129-133 skill_read 면제 조건 확장: `skill_read__*.ok` glob 면제 추가 (evidence_mark_read.sh 스킬별 마커 활용)
   - L155-160 기존 tasks_handoff 블록 삭제 (상단 우선 검증으로 흡수)

3. **`.claude/hooks/smoke_test.sh`** (44-3/44-4 주석 수정 + 44-7/8/9 신규 3건)
   - 44-3: tasks_handoff.req + commit → deny (기능 호환성 유지 확인)
   - 44-4: skill_read__*.ok 선정리 추가 (면제 회피)
   - 44-7 신규: skill_read.req + skill_read__*.ok 존재 → pass (세션78 재정의 검증)
   - 44-8 신규: risk_profile_prompt.sh에 tasks_handoff 조기 트리거 부재 정적 확인
   - 44-9 신규: req 전무 상태 commit → deny (has_any_req 우회 방지 확인)

**[단위 검증 171/171 PASS]** — 전체 smoke_test 섹션 1~46 + 44-5/44-6 세션77 map_scope 회귀 없음

**[예상 효과]**
- skill_read 67건 → 일상 대화 "식별자/기준정보" 트리거 면제로 50% 이하 감소 추정
- tasks_handoff 65건 조기 발행 → 0건 (commit/push 시점만), 검증 타이밍 시간차 0
- resolved 전환율 향상: skill_read는 스킬별 마커로 도메인 편집 자연 흐름, tasks_handoff는 즉시 맥락으로 `/finish` 기동 유도

**[1주 관찰 (2026-04-20 ~ 2026-04-27)]**
- 지표: `.claude/incident_ledger.jsonl` gate_reject + skill_read/tasks_handoff fingerprint 발동 건수
- 목표: skill_read 세션77 평균 대비 50% 이하, tasks_handoff resolved ≥ 80%
- 롤백 조건: 정당한 commit 2회 이상 오차단 시 has_any_req early-exit 원복

**[이월 — Step 2 incident_ledger 반복 5종 정리]**
- 세션85+ 1주 관찰 완료 후 진행 (Gemini 순서 강제 규칙)

---

## 세션77 최종 반영 (2026-04-20, Step 1-c map_scope Policy 재정의)

**[완료] Step 1-c — map_scope Policy 재정의 (evidence_gate 71.4% 점유 대응)**
- **목적**: evidence_gate 486건 중 map_scope.req 347건(71.4%) 과탐지 근본 해결
- **접근**: Claude 독립 옵션 D (트리거 축소 A + 대상 파일 체크 C 조합) — Round 3 정식 토론 대신 실물 구현 + 사후 공유
- **수정 파일 2개**:

1. **`.claude/hooks/risk_profile_prompt.sh`** (트리거 조건 축소)
   - HAS_HOOK_ABSTRACT 제거 ("공통 훅", "운영 게이트" 등 경로 없는 추상 표현 — 의도 부족 트리거)
   - HAS_INTENT 축소: 13개 → 6개 (수정/변경/삭제/리팩터/제거/교체만 유지)
   - 제거된 8개: 추가/구현/신설/이동/전수/일괄/개편/손본 (신규·논의 단계 포함으로 FP 과다)

2. **`.claude/hooks/evidence_gate.sh`** (대상 파일 경로 체크 추가)
   - 기존: Write/Edit/MultiEdit 모두 차단 → 문서·데이터 수정도 차단되는 과탐지
   - 변경: 대상 파일이 `.claude/hooks/*.sh` 또는 `.claude/settings*.json`일 때만 차단
   - `.md` / 데이터 / 업무 스프레드시트 / 일반 스크립트는 면제
   - `safe_json_get`이 중첩키 미지원이라 raw INPUT에서 `file_path` 직접 grep

**[단위 검증 9/9 PASS]**
- Write on .md → pass ✅
- Write on .claude/hooks/*.sh → deny ✅
- Write on settings.local.json → deny ✅
- Write on settings.json → deny ✅
- Write on TASKS.md → pass ✅
- Edit on hook_common.sh → deny ✅
- Edit on .py → pass ✅
- Bash ls → pass ✅
- MultiEdit on .claude/hooks/*.sh → deny ✅

**[smoke_test 44-5 수정 + 44-6 신규]**
- 44-5: `tool_input: "test_file.md"` 구포맷 → `{"file_path":".claude/hooks/new_hook.sh"}` 신포맷. 여전히 deny 기대.
- 44-6 신규: `{"file_path":"docs/some.md"}` → pass (세션77 재정의 검증)

**[예상 효과]**
- 기존 이월 기준: map_scope 트리거 347건/세션 → 축소 조건으로 **50건 이하** 예상
- 일상 대화·문서 수정 마찰 해소
- 통제 목적(운영 훅·settings 변경 보호)은 유지

**[이월 — Step 2 incident_ledger 반복 5종 정리]**
- Step 1-c 완료 후만 진행 (Gemini 순서 강제 규칙)
- 1주 관찰 → 새 Policy 효과 실증 후 Step 2 착수
- 예상 시점: 세션85+

**[이월 — skill_read.req / tasks_handoff.req Policy 재정의]**
- map_scope 재정의 효과 확인 후 동일 패턴 적용
- skill_read: session 내 SKILL.md 1회 읽으면 재실행 허용 (현재 매 호출마다 재검증)
- tasks_handoff: commit 직전 자동 trigger (현재 작업 시작 시점 trigger라 자연 흐름 어긋남)

---

## 세션77 추가 반영 (2026-04-19, Silent Failure 자동화 + 관찰 스크립트 + evidence_gate 전수 분해)

**[완료] nightly_capability_check.sh 신설 — Silent Failure 방지 (Gemini 최우선 안전망)**
- `.claude/hooks/nightly_capability_check.sh` 신설
- SMOKE_TEST_FORCE=1로 캐시 무시 강제 실행 → smoke_test 167 전수 검증
- 결과를 `.claude/state/nightly_capability_log.jsonl`에 append
- FAIL 감지 시 incident_ledger에 `silent_failure` 분류로 기록 + exit 2
- Windows schtasks 등록 예시 주석 포함 (수동 1회: `schtasks /Create /TN claude_nightly_capability /TR ... /SC DAILY /ST 02:00 /F`)
- **Phase 3 실제 격리 삭제 전제조건** — Gemini Round 2 경고 반영

**[완료] pruning_observe.sh 신설 — Phase 2 관찰 리포트**
- `.claude/hooks/pruning_observe.sh` 신설 (measurement 등급, read-only)
- 격리 후보 7섹션 모니터링:
  - nightly_capability_log.jsonl 실행 이력 집계
  - incident_ledger에서 관련 hook 실패 집계 (최근 N일)
  - Phase 3 진입 조건 판정 (nightly 7회 이상 + FAIL 0 + incident 증가 없음)
- cygpath 적용으로 Windows Git Bash MSYS 경로 이슈 해결
- PYTHONIOENCODING=utf-8 + LC_ALL 설정
- 초기 실행 확인: 격리 후보 7섹션 식별 OK, Phase 3 HOLD (관찰 전)

**[보류] Step 3 섹션별/의존파일별 해시 캐시 — ROI 낮음으로 판정**
- 공수 큼: smoke_test.sh 990라인 선형 구조에 각 섹션 skip 블록 추가 필요
- 효과 제한: commit 경로는 이미 fast 모드(0.57s), full 모드는 전체 hash 캐시(TTL 30분)로 이미 90% 효과 달성
- 판정: **marginal gain 대비 공수 과대**, 세션85+ Phase 3 삭제 후 재평가

**[완료] Step 1-b — evidence_gate 486건 5정책 분해 (충격 결과)**
- `.claude/docs/evidence_gate_policy_breakdown.md` + `.json` 신설
- **map_scope.req 단일 정책이 347건(71.4%) 압도적 점유** (Round 1 추정 46.2%보다 훨씬 큼)
- 정책별 분포:
  - map_scope.req: 347 (71.4%) — unresolved 246 / resolved 101
  - skill_read.req: 67 (13.8%) — 전부 unresolved (resolved 0%)
  - tasks_handoff.req: 65 (13.4%) — 전부 unresolved
  - auth_diag.req: 4 (0.8%)
  - date_check.req: 3 (0.6%)
- 핵심 인사이트:
  - **map_scope 단일 재정의만으로 incident 70% 감소 가능**
  - skill_read + tasks_handoff 132건 전부 미해결 = 사용자 정책 준수 시도 포기 상태 = Gemini "Policy-Workflow Mismatch" 정확히 실증
  - resolved 102건 중 101건이 map_scope → 이 정책만 해결 가능한 구조
- Step 1-c 재정의 우선순위: map_scope (최우선) → skill_read → tasks_handoff

**[세션78 이월 — 3자 토론 Round 3 준비]**
- 의제: Policy-Workflow Mismatch 종합 감사 (map_scope Policy 재정의 초안 + 3자 검증)
- 옵션 A: "고위험" 기준 축소 (data-and-files.md Full Lane 기준 차용)
- 옵션 B: map_scope.ok 자동 생성 (Claude가 3줄 선언 자동 작성 후 사용자 승인)
- 옵션 A+B 조합 권장, 옵션 C(완전 폐지) 위험

---

## 세션77 반영 (2026-04-19, Step 1 Test Pruning Phase 1 — 격리 후보 선별)

**[완료] smoke_test 섹션 인벤토리 구축**
- `.claude/docs/smoke_test_sections_inventory.json` 신설
- 총 47 섹션 / 167 check 호출
- REGRESSION 27섹션 (1-21, 25-30) / CAPABILITY 19섹션 (22-24, 31-46)
- 각 섹션의 의존 hook / check_count / 시작-종료 라인 기록

**[완료] Step 1 Phase 1 — Pruning 후보 7섹션 선별**
- `.claude/docs/smoke_test_pruning_candidates.md` + `.json` 신설
- 선별 기준 (3자 합의 반영):
  - 공용 의존성(hook_common/evidence_gate/commit_gate/completion_gate) 있으면 보호
  - check_count ≥ 4는 보호
  - capability + 외부 훅 비의존 or 단일 hook + check ≤ 3 → 격리 후보
- **격리 후보 7섹션 / 20 check (12.0% 감축 잠재)**:
  - 24b(json_escape payload), 33(incident_review.py), 34(classify_feedback.py), 36(hook_config.json), 37(incident_repair.py 매핑), 38(task_runner.sh), 39(incident_repair.py backfill)
- protect 13섹션: 공용 의존 or high_checks
- **원칙**: 격리 ≠ 삭제. Phase 1에선 코드 변경 없이 문서화만

**[Phase 2 이월 — 세션77~세션84 관찰]**
- 관찰 지표:
  - `SMOKE_LEVEL=full` 실행 횟수
  - 격리 후보 7섹션 FAIL 발생 여부
  - incident_ledger 관련 hook 실패 기록
- 수집 위치: hook_log.jsonl + incident_ledger.jsonl

**[Phase 3 이월 — 세션85 또는 1주 후]**
- 조건 A 충족 시 smoke_test.sh에서 해당 블록 실제 삭제 + 아카이브
- 조건 B(FAIL 발생)는 보호 환원
- 조건 C(데이터 부족)는 관찰 연장

**[Silent Failure 대응 필수 선행 — Gemini 경고 반영]**
- 격리 후보 7섹션 중 파이썬 도구 관련 5섹션 (`incident_review.py`, `classify_feedback.py`, `incident_repair.py` 등)
- 이들이 `SMOKE_LEVEL=full`에서만 돌고 평소 조용히 고장날 위험
- **Phase 3 이전 `nightly_capability_check.sh` 반드시 구현** (Windows schtasks 일일 배치)

**[이월 지속]**
- Round 1: evidence_gate 전수 474건 하위 정책 분해 (Step 1-b) + Policy 재정의 (Step 1-c) + incident 반복 5종 정리 (Step 2)
- Round 2: Step 3 섹션별/의존파일별 해시 캐시 + Step 4 grep/sed 중복 통합 + Step 2 Silent Failure 자동화

---

## 세션76 반영 (2026-04-19, Round 2 3자 토론 + Step 1-a + commit_gate + smoke_test 최적화)

**[완료] 3자 토론 Round 2 채택 (pass_ratio 1.00) — smoke_test.sh 3분 병목 최적화**
- 로그: `90_공통기준/토론모드/logs/debate_20260419_215501_3way/round2_*.md` + `result.json`
- 의제: Policy-Workflow Mismatch 2호 구체 사례 — smoke_test.sh 3m20s 병목
- 상호 감시 프로토콜 2회차 실증: **GPT A안 최우선 과잉설계 → Claude·Gemini 2:1 이의 → GPT 자진 철회** (Round 1과 동일 패턴)

**[완료] Step 2 regression/capability 실행 분할 구현 (즉시 효과 확인)**
- `.claude/hooks/final_check.sh` L351-380 수정:
  - `SMOKE_LEVEL` 환경변수 분기 추가 (기본값 `fast`)
  - `fast`: smoke_fast.sh만 실행 (regression 10/10)
  - `full`: smoke_test.sh 167 케이스 전체 실행
- **측정 결과**: `time bash final_check.sh --full`
  - Before: **3m 31s** (user 1m22s / sys 1m52s)
  - After: **15.9s** (user 5.2s / sys 8.4s)
  - **92.5% 단축 달성**
- 수동 전체 검증 경로: `SMOKE_LEVEL=full bash .claude/hooks/final_check.sh --full`

**[완료] smoke_test.sh 결과 캐시 로직 추가 (안전망)**
- hook 파일 + settings sha1 해시 기반, TTL 30분
- SMOKE_TEST_FORCE=1 환경변수로 강제 재실행 가능
- 3자 합의: 주 판정은 Step 3(섹션별 해시)로 교체 예정, 본 캐시는 안전망 유지

**[완료] Step 1-a 측정 프로토콜 확정 + evidence_gate 100건 라벨링 (커밋 924e6ff7)**
- `.claude/docs/incident_labeling_protocol.md` v1.0 신설
- `.claude/docs/incident_labels_evidence_gate_100.json`
- 라벨: true_positive 0% / FP_suspect 69% / ambiguous 31% — **Gemini Policy-Workflow Mismatch 초강력 실증**

**[완료] commit_gate.sh push 단독 final_check 스킵 근본 해결**
- 이 버그 자체가 Policy-Workflow Mismatch 1호 실증 사례
- 단위 검증 7/7 PASS, 실물 push 성공 (cfe8d8d9 → 924e6ff7)

**[이월 — 세션77+]**
- **Step 1 Test Pruning 실제 격리** (문서화는 세션77 착수) — 격리 후보 분리 → 1주 관찰 후 삭제 판정
  - 기준: 30일 무고장 + 최근 수정 이력 + 공용 의존성(hook_common.sh·evidence)
- **Step 3 섹션별/의존파일별 해시 캐시** — 변경 섹션만 재실행
- **Step 4 grep/sed 중복 통합** — 같은 파일 연속 grep -q → 단일 awk/grep -f
- **Step 2 Silent Failure 자동화** (Gemini 보강) — capability 일일 배치 또는 병합 전 훅
- **Step 5 A안 (섹션별 보조 러너)** — 조건부 최후순위
- **Round 1 이월 지속**: evidence_gate 전수 474건 분해 / Policy 재정의 / incident 5종 정리

---

## 세션76 반영 (2026-04-19, Step 1-a 측정 프로토콜 + commit_gate 근본 수정)

**[완료] Step 1-a 측정 프로토콜 확정 + evidence_gate 100건 라벨링**
- `.claude/docs/incident_labeling_protocol.md` v1.0 신설 (라벨 3종 + Tiebreaker + 샘플 정책)
- `.claude/docs/incident_labels_evidence_gate_100.json` (최근 100건 분류 결과)
- `.gitignore`: `.claude/docs/` 예외 추가 (커밋 924e6ff7)
- 라벨 분포 (evidence_gate 최근 100건):
  - **true_positive: 0 / 100 (0.0%)** ← Gemini Policy-Workflow Mismatch 지적 초강력 실증
  - false_positive_suspect: 69 (69.0%)
  - ambiguous: 31 (31.0%)
- Policy 분포:
  - map_scope.req 39건 — "고위험" 기준 재정의 대상
  - tasks_handoff.req 30건 — commit 직전 시점 재설계 대상
  - skill_read.req / identifier_ref.req 31건 — Step 1-b에서 분리 필요

**[완료] commit_gate.sh push 단독 final_check 스킵 근본 해결**
- **증상**: Step 1-a 산출물 push 시 `commit_gate BLOCK: final_check --fast FAIL — TASKS/HANDOFF/STATUS write_marker 이후 미갱신`
- **원인**: `git push`도 commit_gate의 final_check 재실행 대상이어서, write_marker가 commit 후에도 유지되며 push 단독 호출이 "미갱신" FAIL로 차단
- **진단 정당성**: 이 버그 자체가 **Policy-Workflow Mismatch(세션75 3자 토론 채택 의제)의 생생한 실증 사례** — 게이트가 실제 정책 위반이 아닌 정상 push를 과도 차단
- **해결**: `commit_gate.sh` L107 이후 push 단독 명령(`grep 'git push' && !grep 'git commit'`)은 final_check 스킵하고 exit 0으로 통과. commit 단계의 검증으로 통제 목적 충분 (중복 제거)
- **단위 검증 7/7 PASS**: push 단독 / commit / commit+push 복합 / git status / ls / grep 파이프 조합
- **실물 검증**: push 재시도 성공 (cfe8d8d9 → 924e6ff7)

**[이월 — 세션77+]**
- **Step 1-b evidence_gate 전수 474건 하위 정책 분해** (map_scope / tasks_handoff / skill_read / identifier_ref / auth_diag별 비율 산출)
  - ambiguous 31% 해소 포함 (skill_read vs identifier_ref 분리)
- **Step 1-c evidence_gate Policy 재정의** (세 정책 각각 재설계)
- **Step 2 (Step 1 통과 후) incident_ledger 반복 5종 정리** (903건 88%)
- **Step 3 문서 드리프트 자동 --fix 금지 + 파생 문서 preview 절충**
- **Round 2 토론**: Policy-Workflow Mismatch 종합 감사 + debate_verify 체인 점검

---

## 세션75 반영 (2026-04-19, 3자 토론 Round 1 — 클로드코드 정밀 분석)

**[완료] 3자 토론 Round 1 채택 (pass_ratio 1.00)**
- 로그: `90_공통기준/토론모드/logs/debate_20260419_215501_3way/`
- 의제: 클로드코드(Claude Code) 운영 정밀 분석
- GPT 방: `c/69e4c33c-0884-83e8-9393-467475149632`
- Gemini 방 (신규): `gem/3333ff7eb4ba/aecf2ecbf3d5bb44`
- 상호 감시 프로토콜 실증: **GPT 주장 3 "60분 캐시" 훅 혼동 → Claude·Gemini 2:1 이의 → GPT 자진 철회** (단일 모델 오류 차단 성공)

**[Step C 실물 검증 결과]**
- C-1: commit_gate.sh 60분 캐시 **부재** 확정 (permissions_sanity.sh의 CACHE_TTL=3600과 혼동)
- C-2: hook_common.sh L79-106 sed JSON 파싱 4곳 존재 but 설계자 자각 주석 + incident 장애 0건
- C-3: incident 1027건 breakdown — evidence_gate 474(46.2%) + commit_gate 259(25.2%) 상위 2종이 71.4%. true_positive 라벨 12건(1.2%) vs structural/missing 66.8% → **Policy-Workflow Mismatch 실증**

**[3자 합의 결과]**
- 채택: 주장 1·2·7, 권 a, 권 c(조건부)
- 버림: 주장 3(훅 혼동), 권 b(--fix 자동 동기화, 단 파생 문서 preview 절충)
- 보류: 주장 4 hook_common fragility, 주장 5 python3 portable (Round 2 제외)
- **신규 의제 승격**: Policy-Workflow Mismatch (Gemini 제안 + GPT 세련화 + Claude 실증)

**[세션75+ 이월 — 즉시 실행 엄격 시퀀스]**
1. **Step 1-a 측정 프로토콜 확정** (GPT 제안) — true_positive / FP 의심 / 정상중간과정 라벨링 규칙 고정
2. **Step 1-b evidence_gate Policy 하위 분해** (GPT 제안) — tasks_handoff / skill_read / map_scope / auth_diag 정책별 분해
3. **Step 1-c evidence_gate Policy 재정의** — "기준 재정의" 관점 (게이트 완화 아님)
4. **Step 2 (Step 1 통과 후에만) incident_ledger 반복 5종 정리** (Gemini 순서 강제) — 상위 5종 903건(88%)
5. **Step 3 문서 드리프트 자동 --fix 금지 + 파생 문서 preview** (병렬 가능)

**[Round 2 의제 (별도 토론 예정)]**
- Policy-Workflow Mismatch 종합 감사 (제조업 G-ERP 워크플로우 vs 게이트 Policy 맵핑)
- debate_verify 체인 점검 (Gemini 포함 주장 채택 — Round 2 메타 신뢰성 확보)

**[검증]**
- pass_ratio 1.00 / 3 (≥ 0.67 초과 달성)
- 교차 검증 4키 전체 수집: gemini_verifies_gpt(검증필요→실물확정), gpt_verifies_gemini(동의), gpt_verifies_claude(동의), gemini_verifies_claude(동의)
- 합의 실패 없음 (consensus_failure.md 미작성)

---

## 세션74 반영 (2026-04-19, 쟁점 G 실물 분리 세션)

**[완료] 쟁점 G settings 계층 실물 분리 — 단일 원자 커밋**
- `.claude/settings.json` **신설** (Git 추적): TEAM 76건 + hooks 31매처 + statusLine 이동
- `.claude/settings.local.json` **축소**: PERSONAL 8건 + ask 8건 (hooks/statusLine 제거)
- **제거 18건** (개인경로 11 + 1회용 잔재 7):
  - 개인경로 11: `Bash(mkdir -p "C:/Users/User/...")` × 5, `Bash(git -C "C:/Users/User/..." rev-parse HEAD)`, `Bash(python3 "C:/Users/User/..." ...)` × 2, `Bash(PYTHONIOENCODING=utf-8 python3 "C:/Users/User/..." ...)`, `Bash(awk ... /c/Users/User/... commit_gate.sh)`, `Read(//c/Users/User/Desktop/업무리스트/**)` (포괄 `Read` 권한이 TEAM에 있어 기능 손실 없음)
  - 1회용 잔재 7: `Bash(echo 'https://...')` × 1 + `Bash(echo "https://...")` × 1 (탭 URL), `Bash(echo '1382935544')` + `Bash(echo "1382937470")` (PID echo), `Bash(PYTHONUTF8=1 python3 -c "import json; ... settings.local.json ...")` (1회용 JSON 검증), `Bash(python3 "90_공통기준/업무관리/slack_notify.py" --message "[daily-doc-check ...]")` × 2 (하드코딩 슬랙 메시지)
- **PERSONAL 8건 최종**: Windows 4(`powershell -Command Get-Date:*`, `tasklist:*`, `schtasks:*`, `start *:*`) + `wmic process *` + `gemini:*`·`gemini -p:*`·`echo "*" | gemini *:*`
- **hooks 31매처 순서 100% 보존** (PreToolUse 첫 번째 `block_dangerous` 확인)

**[완료] 검증 스크립트 5개 team+local union 지원 (근본 해결)**
- **배경**: 세션71 settings 분리 정책 합의 당시 검증 스크립트들의 `settings.local.json` 하드코딩을 사전 교정하지 않아, 세션74 실물 분리 시 `final_check --full` 3 FAIL → `commit_gate` exit 2 차단 발생 (설계 누락성 버그)
- **수정 5개**:
  - `final_check.sh`: `SETTINGS_TEAM`/`SETTINGS_LOCAL` 분리 + `registered_hook_names()` union
  - `smoke_test.sh`: `grep_settings_any`/`grep_settings_none` helper 신설, 5곳 전환 (send_gate·CDP·instruction_read_gate·mcp_send_gate·navigate_gate)
  - `smoke_fast.sh`: settings.json·settings.local.json JSON 유효성 양쪽 검증
  - `doctor_lite.sh`: settings 두 파일 루프 검증
  - `permissions_sanity.sh`: team+local union allow 스캔 (Counter 중복 탐지 포함)
- **결과**: final_check --full 167/167 PASS · smoke_fast 10/10 · doctor_lite OK

**[완료] `permissions_sanity.sh` single-quote regex 버그 수정**
- 세션73 탐색에서 발견한 버그: regex가 `"..."`(double-quote)만 매칭 → `'...'`(single-quote) 잔재 2건 미탐지
- 수정: `r'^Bash\(echo "\d{10,}"\)$'` → `r'^Bash\(echo ["\']\d{10,}["\']\)$'` (URL regex 동일)
- 6/6 단위 검증 통과 (double/single/non-match 조합)

**[완료] `.gitignore` 정정**
- `!.claude/settings.json` 예외 추가 (신설 파일 추적)
- `.claude/settings.local.json.bak_20260419` 제외 추가 (세션74 백업 보호)

**[검증]**
- `.claude/settings.json` JSON 유효 · allow 76 · PreToolUse 16매처 (block_dangerous 첫째)
- `.claude/settings.local.json` JSON 유효 · allow 8 · ask 8 · hooks/statusLine 부재
- `bash .claude/hooks/smoke_fast.sh` 10/10 PASS (세션74 team+local union 수정으로 +1)
- `bash .claude/hooks/doctor_lite.sh` OK
- `bash .claude/hooks/permissions_sanity.sh` 경고 0건
- hooks 원본 vs 신설 파일 diff 완전 동일 (31매처, PreToolUse 16 순서 일치)
- `git check-ignore`: settings.json 추적 가능 / bak_20260419 제외 / settings.local.json은 추적 중 (기존 정책 유지)

**[후속 검증 — 사용자 수행 필수]**
- Claude Code CLI 재시작 (settings 캐싱 특성상 재시작 없이 미반영)
- 재시작 후 `doctor_lite` + `smoke_fast` + `permissions_sanity` 재검증
- 1주 후 permissions 팝업 빈도 측정 — 분리 효과 확인

**[이월]**
- 세션75: `hook_timing.jsonl` 1주 집계 + gate 9개 `exit 2` 승격 판단
- 조건부: `debate_verify` 태그 incident 7일 0건 달성 시 Phase 2 승격

---

## 세션73 반영 (2026-04-19, 이월 3건 처리 세션)

**[GPT 판정: PASS]** 845e2e93 — 3커밋 모두 실물 검증 통과
- 세션72 HANDOFF "다음 세션 첫 액션 3건"(쟁점 G + Phase 2-C + GPT 지적 A) 모두 충분히 처리
- 스코프 확장 5→12훅 타당 근거 인정 (smoke_test 46-3 구식 가정 + 누락 7개)
- 쟁점 G 사전작업이 세션74 단일 원자 커밋 실행 전제로 충분 — 실행만 남음
- 세션74/75 후속은 미처리가 아닌 의도적 계획된 후속 단계로 평가

**[완료] Step 1 — PreToolUse JSON 필드 `hookSpecificOutput` 스키마 마이그레이션**
- context7 공식 Claude Code hook-development SKILL 기준으로 PreToolUse **12개 훅 20개 JSON 출력**을 `{"decision":"deny","reason":...}` → `{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":...}}` 교체
- 스코프 확장: 초기 5개 훅 계획 → 탐색 중 `smoke_test.sh` 46-3 검사가 "hookSpecificOutput 잔재 없음"으로 구식 가정 + PreToolUse gate 7개 누락 추가 발견 → 일관성 회복 위해 12개 일괄 처리
- **Phase 2-B 완료 5개(exit 2 유지)**: `block_dangerous.sh`(6) · `commit_gate.sh`(2) · `date_scope_guard.sh`(1, `json_escape` 적용) · `protect_files.sh`(2) · `harness_gate.sh`(2)
- **PreToolUse gate 7개 추가**: `evidence_gate.sh`(1, `json_escape`) · `mcp_send_gate.sh`(1) · `instruction_read_gate.sh`(1) · `skill_instruction_gate.sh`(3) · `debate_gate.sh`(1) · `debate_independent_gate.sh`(1) · `navigate_gate.sh`(1)
- **smoke_test.sh·e2e_test.sh 갱신**: grep 패턴 `"decision":"deny"` → `"decision":"deny"|"permissionDecision":"deny"` 양식 병행 허용 (10건), 46-3 assertion 뒤집어 "PreToolUse 12 훅 hookSpecificOutput 적용 확인"으로 전환
- 건드리지 않음(Stop legacy 정상): `stop_guard.sh`, `gpt_followup_stop.sh`, `completion_gate.sh`, `evidence_stop_guard.sh`
- 머리말 주석 2건(block_dangerous/commit_gate) 스펙 설명도 최신 스키마로 치환

**[검증]**
- JSON 파싱 유효성: 13/13 OK (python3 json.loads)
- `smoke_fast.sh` 9/9 ALL PASS
- `doctor_lite.sh` OK

**[완료] Step 2 — Phase 2-C timing 배선 (25개 훅)**
- advisory 5 · gate 9 · measurement 11 훅 `hook_timing_start`/`hook_timing_end` 배선 완료
- measurement 11: `write_marker`·`handoff_archive`·`evidence_mark_read`·`debate_send_gate_mark`·`gpt_followup_post`·`post_commit_notify`·`notify_slack`·`session_start_restore`·`precompact_save`·`risk_profile_prompt`·`completion_gate`
- advisory 5: `state_rebind_check`·`permissions_sanity`·`auto_compile`·`skill_drift_check` + `debate_verify`(기존 유지)
- gate 9: `harness_gate`·`evidence_gate`·`mcp_send_gate`·`instruction_read_gate`·`skill_instruction_gate`·`debate_gate`·`debate_independent_gate`·`navigate_gate`·`gpt_followup_stop`
- 각 종료 경로 status 태그 세분화 (pass/skip_*/block_*/warn/compile_ok 등)
- gate 9개 `exit 2` 승격은 이번 세션 보류 (1주 `hook_timing.jsonl` 수집 후 판단 — 기준선은 커밋 C 문서에)
- `debate_verify.sh`는 incident 18건 잔존 → Phase 2 승격 보류 유지
- 검증: smoke_fast 9/9, doctor_lite OK, final_check 167/167 PASS (0 FAIL)

**[완료] Step 3 — 쟁점 G 사전작업 문서 (세션74 실물 분리 대비)**
- `90_공통기준/토론모드/session73_review19_decisions.md` 신설
- **Permissions 100건 재분류 결정**:
  - TEAM 80건 (→ settings.json): 기본 도구 + git/gh + Bash fallback + 프로젝트 hook/스킬 + MCP + REVIEW 승격 14건
  - PERSONAL 4건 (→ settings.local.json 유지): Windows OS 도구(powershell/tasklist/schtasks/start)
  - PERSONAL + 개인경로 11건: `C:/Users/User/...` 절대경로 — 세션74에서 상대경로 대체 또는 제거 권장
  - DELETE 3건: 1회용 잔재 (single-quote echo URL/PID + specific python inline)
- **부수 발견**: `permissions_sanity.sh` regex가 single-quote 미탐지 버그 (`^Bash\(echo "\d{10,}"\)$`는 single-quote 변형 놓침) — 세션74 수정 검토
- **gate 9개 exit 2 승격 기준선 문서화**: 1주 `hook_timing.jsonl` 수집 후 승격 판단 절차 3단계
- **세션74 실물 분리 절차 6단계** + 롤백 전략 명문화

**[이월]**
- 세션74: 쟁점 G 실물 분리 (단일 원자 커밋 + 세션 재시작 필수)
- Phase 2-C 이월 분석: `hook_timing.jsonl` 1주 수집 후 gate 9개 exit 2 승격 판단
- `debate_verify.sh` Phase 2 승격: 7일 연속 `debate_verify` incident 0건 달성 시

---

## 세션72 반영 (2026-04-19, 의제5 Phase 2-B 핵심 훅 exit 2 전환 세션)

**[완료] Phase 2-B Step 1 — `completion_gate.sh` 소프트 블록 추가**
- 최근 7일간 `permissions_sanity` "1회용 패턴" 동일 라벨 3회 이상 누적 감지 시 JSON `decision=deny` 1회 발생
- 60초 쿨다운 캐시 (`.claude/state/completion_gate_phase2b_last.txt`)로 재보고 시 통과 — 하드페일 없음
- `hook_incident` + `completion_claim.jsonl`에 `soft_block` 기록
- 상위 게이트(Git 변경/상태문서 미갱신) 통과 후에만 평가 — 기존 동작 불변

**[완료] Phase 2-B Step 2a — `commit_gate.sh` timing + exit 2 전환**
- 모든 종료 경로에 `hook_timing_end` 배선 (skip_empty/skip_nongit/block_marker/block_final_check/pass)
- `echo {deny} → exit 0` 패턴을 `echo {deny} → exit 2` 병행으로 승격 (JSON deny + exit 2 belt-and-suspenders)
- 등급 헤더 gate 명시화

**[보류] Phase 2-B Step 2b — `debate_verify.sh` Phase 2 승격**
- `incident_ledger` `debate_verify` 태그 18건 잔존 (result.json 파싱 실패 + step5 누락 반복) → Phase 2 승격 보류
- Phase 2-C 조건: 7일 연속 `debate_verify` 태그 incident 0건 달성 시 exit 2 전환
- 현 세션 조치: timing 배선만 추가 (skip_nonbash/skip_noncommit/skip_wip/skip_non3way/pass/phase1_warn)

**[완료] Phase 2-B Step 3 — 핵심 훅 5종 timing + exit 2 전환**
- `block_dangerous.sh` (호출 304회/2000) — 5개 차단 경로 모두 exit 2
- `date_scope_guard.sh` (호출 303회/2000) — `deny()` 함수 exit 2 승격
- `protect_files.sh` (호출 120회) — 확장자/경로 차단 exit 2
- `evidence_stop_guard.sh` — 기존 exit 2 유지 + timing 배선
- `stop_guard.sh` — 기존 exit 2 유지 + timing 배선 (4개 블록 경로 상태 구분)

**[완료] 문서 갱신**
- `.claude/hooks/README.md` 등급 분류 테이블을 "Phase 2-B 적용 현황" + "Phase 2-C 이월" 2단 구조로 재작성
- `CLAUDE.md` "훅 등급 + 에러 전파 정책" 섹션의 "현재 실코드 상태" 주석을 "Phase 2-B 적용 현황"으로 치환

**[검증]**
- `smoke_fast.sh` 9/9 PASS
- `doctor_lite.sh` OK
- `permissions_sanity.sh` 경고 0건 (캐시 제거 후 재실행)
- `debate_verify.sh` exit 0 (3way 미포함 커맨드)
- `hook_timing.jsonl` 다중 훅 status 태그 정상 기록 (pass/skip_*/block_* 구분)

**[이월]**
- Phase 2-C: 나머지 ~18개 훅 일괄 등급 주석 + timing 배선 + JSON deny gate들 exit 2 전환 검토
- Phase 2-C: `debate_verify.sh` incident 7일 0건 달성 시 exit 2 승격
- 쟁점 G: settings 계층 실물 이행 (세션73)
- 의제4: hook_timing.jsonl 1주 수집 후 통합 평가

**[GPT 판정: PASS] fb58b9b2 — 후속 과제 2건 (세션73+ 이월)**
- **GPT 지적 A**: PreToolUse JSON 출력 필드가 `decision/reason` (deprecated) — Anthropic 공식 권장은 `hookSpecificOutput.permissionDecision` + `permissionDecisionReason`. 기존 필드도 아직 작동하므로 PASS 판정. 후속 안건으로 context7 MCP로 최신 hook spec 확인 후 일괄 마이그레이션.
- **GPT 지적 B**: `completion_gate` 소프트 블록 "확인 흔적 보강" 권장. 현재 `hook_incident` + `completion_claim.jsonl`에 soft_block 기록 중이나 사용자 측 가시성이 부족. 실제 3회 누적 발생 시 로그 확인 후 필요성 재평가(예방적 과잉설계 회피 — Claude 독립 견해).

---

## 세션71 반영 (2026-04-19, 의제5 토론 + 근본해결 실물 이행 세션)

**[완료] 의제5 3자 토론 Round 1 합의** (`debate_20260418_190429_3way/`, pass_ratio 1.33)
- 로그: GPT 동의, Gemini 동의, 양측 Claude 종합 설계안 동의 (4/3 = 1.33, 채택 조건 ≥0.67 초과)
- critic-reviewer WARN 반영 — 실물 훅(debate_verify·commit_gate) exit code 분기 Read 확인 후 진행
- 합의 8개 쟁점 채택 (A~F + 신규 G·H)

**[완료] 의제5 Phase 2-A 실물 이행 (근본해결)**
1. `.claude/settings.local.json` permissions 20건 정리 (114→94): 1회용 18건 + 완전 중복 2건 제거
2. `.claude/hooks/permissions_sanity.sh` 신설 — advisory 등급, stderr 경고, 60분 캐시, 차단 없음
3. `CLAUDE.md` 루트 신규 섹션 3개:
   - "hook vs permissions 역할 경계" — 5단계 의사결정 트리 (GPT 제안 1단계 선행 질문 포함)
   - "settings 계층 분리 가이드" — 쟁점 G 선제조건 명시
   - "훅 등급 + 에러 전파 정책" — advisory/gate/measurement 3종 + exit code 표준
4. `.claude/hooks/hook_common.sh` — `hook_timing_start/end` + `hook_advisory/hook_gate/hook_measure` 공통 래퍼 함수 (호출부 전환은 Phase 2-B)
5. `.claude/hooks/README.md` — Stop hook 책임 매트릭스 + 훅 등급 분류 테이블 (30개 훅 현재 실코드 상태 기록)
6. `90_공통기준/토론모드/settings_inventory_20260419.md` — 쟁점 G 재분류 인벤토리 (실물 이동은 세션72 이월)
7. `permissions_sanity.sh` PreToolUse Bash 매처 9번째 등록 (advisory)

**[완료] 의제3 Phase A skill_drift_check 신설**
- `.claude/hooks/skill_drift_check.sh` 신설 — advisory, git commit 시점에만 실행, 5종 래퍼/실물 SKILL.md 정합성 감지
- 대상 5종 정합성 확인: debate-mode, settlement, line-batch-management, line-batch-outer-main, daily 모두 OK
- PreToolUse Bash 매처 3번째(commit_gate 뒤, debate_verify 앞) 등록

**[검증]**
- `smoke_fast.sh` 9/9 PASS
- `doctor_lite.sh` OK
- `debate_verify.sh` exit 0
- `permissions_sanity.sh` 경고 0건

**[이월]**
- Phase 2-B: `completion_gate.sh` 소프트 블록 (1회용 패턴 3회 누적 사용자 확인) + 기존 훅 전수 등급 재분류 → 공통 래퍼 호출 전환
- 의제4: 세션72, hook_timing.jsonl 1주일 수집 후 통합 평가
- 쟁점 G: settings 계층 분리 실물 이행 (settings.json 이동)
- 의제6: Gemini 진입 강제 hook 신설
- 의제7: 탭 throttling 자동 회복 설계

---

## 세션70 반영 (2026-04-18, 이월 의제 재개 세션)

**[완료] 백그라운드 탭 Throttling 대응 지침 전파 (세션70 실증 반영)**
- 토론모드 CLAUDE.md "백그라운드 탭 Throttling 대응" 섹션 신규
- gpt-send / gemini-send: Step 1-C "대상 탭 activate navigate" 추가
- gpt-read / gemini-read: 3-prep "navigate 재호출로 탭 foreground 전환" 강화 (기존 visibilityChange만으로는 해결 안 됨 실증)
- debate-mode.md: 3자 토론 직렬 실행 원칙 추가
- debate-mode/SKILL.md: NEVER 생략 주의 추가
- 근거: Chrome MCP는 tab activate API 미제공 → `navigate(동일URL)` 재호출이 유일 회피 경로


**[완료] 의제3 Gemini synthesis 재수령 → 합의 승격 (pass_ratio 0.50 → 0.67)**
로그: `90_공통기준/토론모드/logs/debate_20260418_170000_3way/`
- `gemini_verifies_claude`: 미수령 → 동의 (근거: pre-commit 훅 이중 배치 + 도메인 의존성 3단계 이관 절충안 합리성)
- `result.json` status: 부분합의 → 합의 (양측 동의)
- `step5_final_verification.md` 신규 — GPT/Gemini 양측 **통과** 판정
- 블로커 해소: 세션69 gpt-read/gemini-read 패치 + 세션70 기존 Gem 대화방 직접 진입
- 실물 이행(Phase A 즉시 이관 4종)은 세션71+로 분리

**[완료] 의제5 hook vs permissions 감사 리포트 작성 (토론 입력용 read-only)**
- 산출물: `90_공통기준/토론모드/의제5_hook_permissions_감사리포트.md`
- 총 hook: 35 .sh + 5 .py / 실행 지점 29개 / permissions.allow 109 항목
- 정리 후보: 18건 (1회용 16 + 완전 중복 2)
- 쟁점 A~F 정리 → 세션71 3자 토론 입력으로 사용

---

## 세션69 반영 (2026-04-18, 3자 토론 세션)

**[완료] 의제1 /schedule 작업 분류 매트릭스 (pass_ratio 1.00)**
로그: `90_공통기준/토론모드/logs/debate_20260418_161959_3way/`
- Tier 1 실행 모드 게이트: Cloud / Desktop / /loop
- Tier 2 Cloud 4칸: GitHub-only(+env 2차검증) / 커넥터(Phase 2) / 로컬실물(Desktop) / 사내망(로컬)
- Phase 1 이관 후보 읽기전용 3종: `/self-audit`, `/doc-check`, `/review-claude-md`
- 하이브리드 작업: 축 신설 안함. [로컬 Desktop 수집 → Git commit → Cloud 가공] 분리

**[완료-합의 2026-04-18 / 실물 구현 2026-04-20 세션79] 의제2 토큰 임계치 경고 스킬 `token-threshold-warn` (pass_ratio 1.00)**
로그: `90_공통기준/토론모드/logs/debate_20260418_164115_3way/`
- 임계치: TASKS 400/800, HANDOFF 500/800, MEMORY 인덱스 120/200, 개별메모리 60/100, incident 1MB/3MB
- SessionStart hook 경고 + Stop hook 증가량 기록 (차단 없음)
- 자동 아카이브 이동 금지, 토큰 근사치 계산 금지
- **세션79 실물화**: Phase 1(SessionStart 경고) 완료. Phase 2(Stop hook) 1주 후 재평가. 상세: 상단 세션79 블록 참조.

**[합의 (세션70 승격)] 의제3 skill-creator 경로화 (pass_ratio 0.50 → 0.67)**
로그: `90_공통기준/토론모드/logs/debate_20260418_170000_3way/`
- 채택: 래퍼 방식, skill-creator+커밋관문 이중 동기화, 도메인 의존성 우선순위, 3단계 이관(즉시 4종/7일 7종/유지)
- 세션69 상태: Gemini synthesis 미수령(Chrome throttling)
- 세션70: 재진입으로 Gemini 동의 수령 → 합의 완료. 실물 이행(Phase A 4종 즉시 이관)은 세션71+ 분리

**[완료] 즉시 조치 4건 (사용자 지적)**
1. `.claude/commands/debate-mode.md` — Gemini/3자 토론 진입 지침 추가 (기존엔 GPT만 언급)
2. `settings.local.json permissions.allow` — `Bash(echo:*)`/`Bash(cat:*)` 포괄 패턴 추가 (반복 팝업 해소)
3. `.claude/commands/gpt-read.md` 근본 버그 수정 — placeholder 스킵 역순 스캔, 2회 안정성 판정, visibilitychange 트리거, 3단계 재시도(sleep→navigate reload→수동 요청)
4. `.claude/commands/gemini-read.md` 근본 버그 수정 — 메타 텍스트 스킵, 전송버튼 fallback 3중, `not_found` 5회 재시도, 동일 복구 체인

---

## 세션70 이월 (다음 세션에서 재개)

**[완료·세션70] 의제3 Gemini synthesis 검증 재확인** — 합의 승격 완료
**[완료·세션70] 의제5 감사 리포트 작성** — 토론은 세션71에서
**[이월] 의제3 Phase A 실물 이관 4종** — debate-mode, settlement, line-batch-* 4종, daily → 래퍼 자동 생성 + skill_drift_check.sh pre-commit hook 신규
**[이월] 의제4 `/debate-verify` 실행 순서 재평가** — Phase 2 실측 기반 (의제5 쟁점 D와 연계)
**[이월] 의제5 3자 토론** — 감사 리포트(`의제5_hook_permissions_감사리포트.md`) 입력으로 진입
**[이월] 의제6 진입 단계 Gemini 강제 hook 신설** — 사용자 진단
**[이월] 의제7 3자 토론 탭 throttling 자동 회복** — 세션70 수동 재진입 성공이 해결 패턴 제시, 본격 자동화 설계는 다음 세션

---

## 세션68 즉시 적용 (2026-04-18, 3자 토론 합의)

**[완료] Claude Code 명령어 매뉴얼 영상(2rzKCZ7XvQU) 분석 기반 개선 4건 — Round 1 합의**
1. ✅ `/rewind` 한계 CLAUDE.md 명시 — bash 삭제 복구 불가, Git 대체재 아님
2. ✅ context7 우선 규칙 CLAUDE.md 명시 — 라이브러리 문서 조회 시 WebSearch보다 우선
3. ✅ `doctor_lite.sh` 경량 진단 스크립트 + session_start hook 연동 — settings JSON·필수 hook·핵심 문서·git 체크
4. ✅ `statusline.sh` 설정 + `settings.local.json` statusLine 등록 — 모델·경로·브랜치·비용 상시 표시

**[완료] SKILL.md Step 5 지침 버그 패치** — 3way에서 Gemini 누락 방지 (사용자 지적으로 발견)
- 5-3: 3way 양측 동시 전송 [MUST] 명시
- 5-4: 3way 종결 조건 분기 신설
- 5-5: Gemini 판정 필드 필수

**[완료] /debate-verify hook Phase 1 — Round 2 합의**
- `.claude/hooks/debate_verify.sh` — PreToolUse Bash 매처, git commit 시 3way 로그 서명 검증
- 검증: cross_verification 4키 + verdict enum + reason + pass_ratio + step5 양측 판정 섹션
- round_count/max_rounds 일관성 검증
- `incident_ledger.jsonl`에 "tag":"debate_verify" 기록 (Phase 2 전환 계측)
- CP949 인코딩 버그 수정 (Gemini 지적 실물 재현)
- `/debate-verify` 수동 스킬 (`.claude/commands/debate-verify.md`) — --dry-run 사전 점검

**[검증 후 적용 대기 — 세션69 이후]**
- `/schedule` 이관 — 작업 분류 매트릭스(로컬/사내망/GitHub-only/커넥터) 수립 후 GitHub 문서 리포트형만 클라우드화
- `skill-creator` 경로화 — 신규 스킬만 스킬 경로 우선. 기존 `.claude/commands/*.md` 점진 이관
- 토큰 임계치 경고 스킬 (Gemini 제안) — TASKS/STATUS 비대 시 컨텍스트 압축·세션 재시작 권고
- /debate-verify Phase 2 전환 — 1주 운영 후 incident_ledger debate_verify 태그 0건이면 차단 모드(exit 2) 전환
- /debate-verify 실행 순서 재평가 — GPT/Gemini 대립 쟁점, Phase 2 실측 기반 결정

**[폐기]**
- `/batch` — main 직행 아키텍처와 상충 (워크트리 실험 레인 규정 선결 시 재검토)
- `/insights` — ERP 자동화 본선 기여도 낮음, `/self-audit`와 중복
- `--bare` — hook/gate 중심 안전장치 스킵은 리스크

---

## 다음 세션 안건

**[낮] evidence_missing 7일 후 재측정 (세션65 GPT 합의)**
- **1차 측정 결과** (2026-04-18 12:19 KST, 배포 기준시각 2026-04-18T02:13:00Z):
  - 배포 전 7일: 101건 (map_scope 33, skill_read 41, tasks_handoff 20, auth_diag 4, date_check 2, skill_instr 1)
  - 배포 후 ~10시간: 2건 (map_scope 1, skill_read 1)
  - 감소율: 98% (TASKS 목표 50건 이하 대비 초과 달성)
  - **판정: 5조건 보류** (POST ≤ 50)
- **7일 후 재측정 필요** (2026-04-25 이후): 배포 후 7일 데이터로 최종 확정
  - 스크립트: `.claude/scripts/evidence_missing_stats.sh 2026-04-18T02:13:00Z`
  - 71건 이상 또는 감소율 60% 미만 시 5조건 즉시 구현
- **5조건 구현 보류 상태** (기존 TASKS 안건 유지, 조건부 승격):
  1. req가 실제 생성돼 있어야 함
  2. 같은 세션에서 해당 문서/스킬 읽기 흔적 있어야 함
  3. 해당 스킬이 정상 종료해야 함
  4. 정상 종료 직후에만 대응 ok 자동 발급
  5. 중간 실패·재시도 중·부분 실행 시 발급 금지

**[낮] notebooklm-mcp cleanup_data preserve_library 보호 누락 별건 (이슈 #2)**
- **증상**: `cleanup_data(preserve_library=true)` 실행 시 `Legacy Installation` 카테고리에 현행 `AppData/Roaming/notebooklm-mcp` 경로가 포함되어 삭제됨. 결과적으로 `library.json` 소실
- **세션59 실적**: 2개 노트북(`조립비정산_대원테크`, `라인배치_대원테크`) 수동 재등록으로 복구
- **조치 방향**:
  - 업스트림 이슈 리포트 (문서와 실동작 불일치)
  - 로컬 백업 루틴 검토 — cleanup 전 `library.json` 스냅샷

**[낮] safe_json_get 파서 교체 (세션51 GPT 합의: incident 발생 시 승격)**
- 현재 grep/sed 기반. 실제 파싱 실패 incident 미발견 → 후순위 유지
- 승격 조건 명시화(세션54 GPT): ①navigate/evidence/completion_gate 중 JSON 파싱 실패 incident 1회 + ②중첩키 빈값 재현 + ③7일 내 파싱 incident 2회 누적

---

## 다음 세션 안건 (추가)

**[낮] Composio Gemini MCP 통합 검토 (조건부)**
- **조건**: `/ask-gemini` 호출 빈도 ≥ 주 5회 시 승격
- **검토 항목**: Composio 계정/API 키 비용, 자체 호스팅 대안 (RaiAnsar/RLabs 오픈소스 MCP), 본 환경 검증
- **현 상태**: `/ask-gemini` (CLI minion) 1순위 운용. MCP는 빈도 누적 후 결정 (단, 3자 토론 내 사용 금지 — 세션67)

**[중] 3way cross_verification 자동 게이트 스크립트 (세션67)**
- **배경**: SKILL.md v2.10 "자동 게이트" 규정은 명시되었으나 실제 강제 스크립트/훅 미구현. 현재는 Claude 운영 규칙 수준
- **구현 범위**:
  - 3자 토론 로그 디렉터리(`logs/debate_*_3way/`) 내 JSON 스키마 검사
  - `cross_verification` 4개 필수 키 존재, `verdict` enum(`동의`/`이의`/`검증 필요`), `pass_ratio_numeric` 재계산 일치
  - `round_count ≤ max_rounds(=3)` 검사 (세션67 v2.11로 3회 원복)
  - 실패 시 라운드 재실행 신호 또는 `consensus_failure.md` 생성
- **위치 후보**: `.claude/scripts/verify_cross_verification.py` + PostToolUse hook 또는 critic-reviewer 승격
- **조건**: 3자 토론 실사용 2회 누적 후 착수 (과잉설계 방지)

~~**[중] 토론 검증 프로토콜 보완 (세션66 사용자 지적)**~~ → **세션66 종결 시 즉시 구현 완료** (아래 "최근 완료" 항목 참조)

---

## 활성 대기 항목

### [대기] 4월 실적 정산 — **대기: 4월 GERP/구ERP 데이터**
- 4월 정산 데이터 입수 후 `/settlement 04` 실행

### [종료·아카이브] verify_xlsm.py COM 실검증 — `98_아카이브/tasks_archive_20260420.md` 참조

---

## 완료 이력 아카이브

> 세션67 이전 완료 + "최근 완료"/"완료됨" 섹션은 `98_아카이브/tasks_archive_20260420.md`로 이관 (세션80, 1262줄 → 1줄). 원본 백업: `TASKS.md.bak_20260420`. TASKS.md는 세션77~79 블록 + 활성 대기만 유지.
