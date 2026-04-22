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

최종 업데이트: 2026-04-22 — 세션91 (Plan 단계 III 구현 착수)

---

## 세션91 (2026-04-22) — Plan 단계 III 2자 토론 + 구현 (게이트 3종 재절단)

**[완료] 2자 토론 4라운드 — 단계 III 설계 합의**
- 로그: `90_공통기준/토론모드/logs/debate_20260422_stage3_2way/` (round1~4 + SUMMARY.md)
- Round 1: Claude 독립 점검 5의제 제시 → GPT 5의제 전부 채택 (단 의제 1/4/5 Claude 초안 수정 요구)
- Round 2: 합의 확정안 → GPT 조건부 통과 (D 커밋 standalone 1회 조건)
- Round 3: 조건 수용 + 종결 선언 → GPT 최종 통과
- Round 4: Step 4b critic-reviewer WARN 제기(의제 4 "실증됨" 라벨 과대 부여) → GPT 실측 근거로 critic 지적 기각 + 사유 문구 교체 합의
- 채택 누계: 11 / 보류 0 / 버림 0

**[진행중] 단계 III 구현 — 4커밋 순차 착수**
- [완료] 커밋 A (1935efd8): `commit_gate.sh` L81-98 제거 + `final_check.sh` statusLine 제외 + README/STATUS 드리프트 동기화
- [완료] 커밋 B (96b14617): `evidence_stop_guard.sh` L63-70 제거 (latent completion branch 정리)
- [진행] 커밋 C: `evidence_gate.sh` suppress 라벨 `suppress_reason=evidence_recent` 고정
- 커밋 B: `.claude/hooks/evidence_stop_guard.sh` L63-70 제거 (사유: tasks_handoff req producer 제거 이후 latent completion branch 정리 + completion 책임 단일화. 실측 grep `touch_req.*tasks_handoff` 0 matches)
- 커밋 C: `.claude/hooks/evidence_gate.sh` suppress 라벨 hook_log/stderr에 `suppress_reason=evidence_recent` 고정
- 커밋 D: `.claude/hooks/gate_boundary_check.sh` 신설 (standalone 1회 → 오탐 확인 + `# [gate-boundary-allow]` 화이트리스트 → smoke_fast 편입)
- 각 커밋 직후 smoke_fast 10/10 PASS 검증, 실패 시 즉시 revert

**계획 파일 갱신**: `C:/Users/User/.claude/plans/glimmering-churning-reef.md` Part 3 단계 III 세션91 합의 반영 완료

---

## 세션90 (2026-04-22) — 자기유지형 시스템 재설계 (Plan glimmering-churning-reef)

**[진행중] 2자 토론 기반 Self-X 자동 개입 폐기 + 수동 selfcheck 전환**
- 계획 파일: `C:/Users/User/.claude/plans/glimmering-churning-reef.md` (Part 0~8 + 보강안 A~D)
- 2자 토론: Claude × GPT 5라운드 (Round 4에서 누락 14건 + Round 5에서 2건 추가 식별)
- 사용자 선택: 안전안 (자기학습 포기 + 자기유지 보장). 메타 깊이 = 0 엄격 해석

**[완료] 단계 0 — baseline + invariants waiver (8924431d)**
- 0-1: incident baseline snapshot (unresolved 516 / gate_reject 376) → `90_공통기준/업무관리/baseline_20260422/incident_baseline.json`
- 0-2: invariants.yaml settings_drift WARN 임시 비활성화 (단계 V 완료 시 복원)
- 0-A: 활성 훅 37개 dep graph matrix → `baseline_20260422/dep_graph.md`
- 0-C: smoke_fast 10/10 PASS, doctor_lite OK, health_check 3 OK·5 WARN

**[완료] 단계 I — leaf hook 등록 해제 (82be4ab0 → 2300ceb9)**
- I-1 `quota_advisory.sh` (PostToolUse) · I-2 `self_recovery_t1.sh` (Stop)
- I-3 `circuit_breaker_check.sh` · I-4 `health_check.sh` (SessionStart)
- I-5 `session_start_restore.sh` last_selfcheck freshness 표시 + Self-X marker cleanup

**[완료] 단계 II — 감시 게이트 + dead config 정리 (ddef9b77, 471c07a8)**
- II-1 `health_summary_gate.sh` (UserPromptSubmit) 등록 해제
- II-2 `project_keywords.txt` → `98_아카이브/session89_glimmering/project_keywords_20260422.txt`

**활성 훅**: 36 → **30** (SessionStart 3→1 / UserPromptSubmit 2→1 / PostToolUse 8→7 / Stop 5→4)
**회귀**: 전 커밋 smoke_fast 10/10 PASS

**[대기] 다음 진입점 — 단계 III (게이트 3종 재절단)**
- 세션 재시작 후 체감 확인 선행 (권장 경로)
- III-1 commit_gate → Git/staging만 / III-2 evidence_gate → 사전 근거만 / III-3 completion_gate → 최종 완료 선언만
- III-4 `gate_boundary_check.sh` 신설 (금지 토큰 검사)
- III-5 write_marker / evidence_mark_read / evidence_stop_guard 동반 정리

**[완료] origin/main push 복구 (c99c9a16)**
- 배경: GPT Round 재검증 FAIL ("settings.json 여전히 옛 상태") 수령 후 로컬 Git 상태 점검에서 이상 발견
- 진단: 로컬 `refs/heads/main`이 `0000...0000` null 손상 (reflog·HEAD는 정상)
- 조치: `git update-ref refs/heads/main c99c9a16` loose ref 복원 → `git push origin main` 8커밋 일괄 반영 (`ddcb252a..c99c9a16`)
- GPT 원격 재검증: 양측 통과 (SessionStart/UserPromptSubmit/PostToolUse/Stop 훅 unregister 전부 Git 실물 확인)
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260422_095321/`

**[완료] gpt-read.md Step 1 drift 수정 (3497b42e)**
- 배경: 세션90 작업 중 "gpt 대화방 입장" 지시에서 stale `debate_chat_url` ("토론모드 코드 분석") 재사용으로 잘못된 방 진입 사건
- 원인: `gpt-read.md:10` "탭 없으면 debate_chat_url 직행" 구조. 토론모드 CLAUDE.md 27행 "매 세션 프로젝트 최상단 자동 탐지" 규칙 미반영
- 조치: Step 1-A 신설(프로젝트 URL navigate → `main` 스코프 + slug 기반 최상단 href 탐지 → debate_chat_url 갱신), 1-B fallback 분리
- GPT 2자 토론 Round 1 조건부 통과(slug 검증·fallback 지시) → Round 2 PASS (양측)
- 하네스: 채택 4건 / 보류 0 / 버림 0

---

## 세션89 (2026-04-21)

**[완료] Notion API `after` → `position.after_block` 마이그레이션**
- 배경: context7 공식 문서에서 `PATCH /v1/blocks/{id}/children` 의 `after` 파라미터 deprecated 확인
- 수정: `notion_sync.py:684` heading 블록 뒤 children 삽입
- 수정: `notion_sync.py:1466` SYNC_START 뒤 snapshot 삽입
- 변경 전: `{"children": [...], "after": "<block_id>"}`
- 변경 후: `{"children": [...], "position": {"type": "after_block", "after_block": {"id": "<block_id>"}}}`
- 커밋: `0521cc49`

---

## 세션88 (2026-04-21, 세션87 A분류 이월 처리)

**[완료] PROJECT_KEYWORDS 외부 설정 파일 분리 — 양측 PASS**
- 배경: 세션87 Layer 1 B1 Step5 GPT A분류 후속. `.claude/hooks/health_summary_gate.sh:28` 하드코딩 키워드를 외부 파일로 분리
- 신규: `90_공통기준/project_keywords.txt` (주석·빈줄 허용, grep -E OR 결합)
- 수정: `health_summary_gate.sh` — 파일 로드 + 부재 시 하드코딩 fallback (advisory 특성 exit 0 보장)
- 수정: `CLAUDE.md` Self-X Layer 1 — 키워드 목록 출처 기재
- 커밋: `618f46a2` + `bdba5040` + `a74981d1` (정규식 이스케이프 주의 — GPT A분류 반영)
- 검증: 인사 exempt / 프로젝트키워드 주입 / 파일 부재 fallback / smoke_test 215/215 PASS
- 판정: GPT PASS (1차 FAIL은 미푸시 오판 → 푸시 후 재검증 PASS) / Gemini PASS
- 하네스: 채택 3 (정규식 이스케이프 A분류 실증됨) / 보류 0 / 버림 0

**[이월 유지] B3 Self-Evolution (Layer 3)** — B2 안정화 4주 모니터링 후 토론 권고. 로그: `debate_20260421_152101_3way/`

**[완료] Notion 동기화 범위 확장 — 3자 토론 만장일치(pass_ratio 1.0) + Auto 페이지 분리 재설계**
- 의제: 세션86 sync_from_finish()의 "동기화 시각 1줄만 갱신" 설계로 STATUS 본문 2주 정체 (세션45/훅23/smoke 140 고정)
- 3자 토론 로그: `90_공통기준/토론모드/logs/debate_20260421_160431_3way/`
- 합의안 B+' 7묶음: SYNC_START/END marker + position.after_block 전환 + 세션경계 제목 갱신 + 제목실패 반환값 승격 + 편집금지 헤더 + notion_snapshot.json + 마커 자동 재생성
- 사용자 "삽질" 지적 → **근본 재설계 A안 (Auto 페이지 분리)** 전환
  - 신규 Auto 페이지 2개 자동 생성 (notion API POST /pages):
    - `📊 STATUS (Auto)`: 349fee670be88124a65dc740b1f1d0fe
    - `✅ TASKS (Auto)`: 349fee670be88140aaefcffb243a31d2
  - historical 페이지(331fee...)는 수기 기록 보존, 건드리지 않음
  - legacy regex 덮어쓰기 땜질 제거
- STATUS (Auto) — 실질 운영 현황:
  - System Health (invariants 8개 OK/WARN/CRITICAL 아이콘)
  - 핵심 지표 (session/SHA/훅/커맨드/smoke)
  - Circuit Breaker (잠금/trip/T1·T2 한도)
  - 최근 Self-Recovery (auto_recovery.jsonl 5건)
  - 미해결 Incident 상위 (최근 7일)
  - 최근 커밋 10건
- TASKS (Auto) — 작업 목록:
  - 작업 요약 (진행/대기/완료)
  - 세션별 완료 이력 toggleable heading 20건 + 전체 22건 목록
  - 각 세션 body에 완료·커밋·판정·하네스 세부
- 자동 동기화: `/finish` 4.5단계에서 `sync_from_finish()` 호출 → 매 세션 반영
- 커밋: `17f159c0` (SYNC zone 1차) + `587f6a4e` (Auto 페이지 분리 + STATUS 확장)

---

## 세션87 (2026-04-21, Self-X 4-Layer 도입 Phase A + 학습루프 점검)

**[완료] Self-X Layer 1 Self-Detection — 3자 토론 만장일치 통과 + 구현·검증 완료 (2026-04-21 오후)**
- 배경: 사용자 본인 진단 "운영 너무 힘들다 / 어디 고장났는지 모르겠다" → 자가 진단/복구/진화 시스템 도입 결정
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260421_133506_3way/` (agenda + round1~3 + cross_verification + step5)
- 판정 이력: R1 양측 독립 비판 → R2 GPT 조건부·Gemini 통과 → R3 양측 통과 (pass_ratio=1.0) → Step5 GPT 조건부 → A분류 3건 보정 → Step5 양측 통과 (pass_ratio=1.0)
- 채택안 구현 (16 파일):
  - `90_공통기준/invariants.yaml` — 8 invariants + 5 정책 + 4 메커니즘 명세
  - `.claude/self/diagnose.py` — invariants 평가 엔진 (391 라인, OS timeout 격리, 1세션 캐시)
  - `.claude/hooks/health_check.sh` — SessionStart hook ([System Health] stderr 주입)
  - `.claude/hooks/health_summary_gate.sh` — UserPromptSubmit advisory (프로젝트 키워드 매칭 시만)
  - `.claude/settings.json` — SessionStart + UserPromptSubmit 등록
  - `CLAUDE.md` — Self-X Layer 1 health summary 의무 조항
- 커밋: `9cb8e740` (선행 정리) + `fa03658b` (Layer 1 구현) + `e1718a27` (A분류 보정)
- 첫 실행 즉시 가시화 효과 (사각지대 해소 입증): 3 OK · 5 WARN
  - WARN: mes(270.6h)·uncommitted(187.5h/25건)·incident(470)·session_kernel(27.6h)·settings_drift
- 분리 의제: B5 Subtraction Quota (hook≤36, skill≤50, memory≤30) — 별도 토론

**[완료] 학습루프 점검 + incident_ledger 정리 (2026-04-21)**
- incident_ledger.jsonl: surrogate 정규화(603 라인) + backfill_classification(미분류 59→0) + auto_resolve(485건 해소, 미해결 954→469)
- debate_verify 미해결 2건 → 0건 (debate_20260421_102644_3way result.json+step5 생성, debate_20260420_010101_3way 기존 result.json resolved)
- 7일 학습루프 분석: evidence_missing 298건/send_block 84건/pre_commit_check 32건/harness_missing 26건
- 4-Layer Self-X 도입 플랜: `C:\Users\User\.claude\plans\wobbly-prancing-forest.md` (Phase A 완료)

**[완료] 추가 의제 (세션87 오후)**
- B5 Subtraction Quota — 양측 만장일치 (커밋 eaf19586). protected_assets.yaml + quota_diagnose.py + quota_advisory.sh
- B4 Self-Limiting (Layer 4) — 양측 만장일치 (커밋 e076e562). circuit_breaker.json + meta.json + circuit_breaker_check.sh
- B2 Self-Recovery (Layer 2 T1) — 양측 만장일치 (커밋 3672f17f). self_recovery_t1.sh (Stop hook) + auto_recovery.jsonl

**[이월] 다음 세션**
- B3 Self-Evolution (Layer 3) — Round 1 송부 후 사용자 지시 중단. agenda.md에 Claude 독립의견·5질문 보존. 로그: `90_공통기준/토론모드/logs/debate_20260421_152101_3way/`. **B2 안정화 4주 모니터링 후 토론 권고**.
- (A 분류 후속) PROJECT_KEYWORDS 별도 설정 파일 분리 — GPT Step5 추가제안. 1세션 내 처리 가능.

---

## 세션86 (2026-04-21, Notion 동기화 정상화 3자 토론 + incident Case A)

**[완료] Notion 동기화 정상화 — 3자 토론 최종 만장일치 통과 (2026-04-21 오후)**
- 배경: 세션45~86 (7일/41세션) Notion 미동기화 사건. 원인: `.claude/commands/finish.md:35-39` 3.5단계 명세가 `/share-result` 위임 구조에 묻혀 미실행
- 3자 토론 로그: `90_공통기준/토론모드/logs/debate_20260421_102644_3way/`
- 판정 이력: Round 1 GPT 조건부·Gemini 통과 → Round 2 GPT 조건부(wrapper)·Gemini 통과 → Round 3 양측 **통과**
- API 병렬 교차검증 (β안-C): 6-2·6-4 양측 "동의" (단서 없음)
- 채택안 구현:
  - `notion_sync.py` — `sync_from_finish()` wrapper 신설 (events 없이 요약+부모만 갱신, 허위 이력 차단) + `--manual-sync` CLI
  - `finish.md` — 3.5 제거, 4.5 신설 (커밋+푸시 후 Notion 동기화, 9단계 체제, Git 원본주의 보호)
  - `share-result.md` — Notion 비위임 주석
  - `smoke_test.sh` — 섹션 52 3축 배선 검증 + 52-(b) 강화 (실제 호출 패턴 전수 차단)
- 커밋: `425cf186` (Round 1 구현) + `9d3bc66b` (Round 2 보정)
- smoke_test 215/215 ALL PASS
- 실측 동기화 실행: `python notion_sync.py --manual-sync` → Notion MCP fetch 확인 (STATUS 요약 "2026-04-21 11:28 KST" 반영)

---

## 세션86 선행 (incident 근본 개선 실측 + 2자 토론 + Case A 구현)

**[완료] 2자 토론 Round 1 — Case A (GRACE 120→300) GPT 조건부 통과**
- 로그: `90_공통기준/토론모드/logs/debate_20260421_082410/` (agenda + round1_gpt)
- GPT 모델: gpt-5-4-thinking (확장추론 ~80s)
- 판정: 조건부 통과 (방향 맞음, A 분류 확정, 세션83 합의 경계 내)
- 수정 항목 2건: smoke 섹션 51에 299s/301s 경계쌍 + evidence_gate 주석에 세션86 근거
- Claude 하네스: 채택 3 / 보류 1 (90~119s 하위 경계, 우선순위 낮음) / 버림 0
- critic-reviewer: WARN (하네스 채택 2·3번 "실증됨" 라벨 + 0건감사 — Step 5 진행 허용, SHA 소급 기재 조건)

**[완료] Case A 실제 구현 — `evidence_gate.sh` GRACE_WINDOW 120→300**
- 변경: `.claude/hooks/evidence_gate.sh:59` 단일 상수 + 세션86 근거 주석 7줄 추가
- 불변: deny 경로, fingerprint 정의(reason:0:80|command:0:50), fresh_ok 역방향 방어
- smoke_test 섹션 51 신설 (6건, 6/6 PASS): GRACE=300 + 주석 근거 + 경계쌍 + fp 정의 + deny 라벨 + fresh_ok 회귀
- 섹션 48-1 회귀 연계 수정: `GRACE_WINDOW=120` grep → `GRACE_WINDOW=30` 부재 체크 (세션83 Round 2 의도 유지)
- smoke_test 전체 210/212 PASS (남은 2 FAIL은 세션80부터의 선행 이슈 — README 훅 개수·classify_feedback --validate, 본 변경 무관)

**[완료] incident_ledger 실측 집계 (세션85→86 증분 10건)**
- 산출: `90_공통기준/업무관리/incident_improvement_20260421_session86.md` (245줄)
- 증분 tag: α 5 + β 4 + γ 1
- 11:38~11:48 10분 클러스터 7건 연속 간격 [122,119,135,209,5,4] — GRACE 120 경계 탈출 실증

**[완료] fingerprint suppress 효과 측정 (7일 evidence_gate 272건, 249 간격 샘플)**
- GRACE=120 설계가 81.5% 반복을 놓침. 실측 median 347s
- Top3 fp(7일 194건=71%) median 320~370s, over-120 82~93%
- GRACE 300 확장 시 기대 억제율 46.2% (2.5배)

**[완료] completion_gate 52건 분석 — Case C 보류 확정**
- 최근 7일 발동 0건, 현행 소프트 블록 정책 정상 동작

**[이월·세션87+] 2주 관찰 기간 (2026-04-21 ~ 2026-05-05)** — Top3 fingerprint 억제율 변화 측정 → Case B 필요 여부 판단

**[이월·세션87+] 90~119s 하위 경계 smoke 보조 테스트** — 2자 토론 보류 항목. 필요 시 추가

**[완료] γ 1건 line 1198 원인 추적**
- 결과: 코드 결함 아님. `debate_verify.sh` advisory phase 1의 alternative schema(`tag`/`phase`/`count`/`issues`) 정상 레코드
- 본 보고서 분석 스크립트가 `r.get("hook")` 단일 필드만 보고 None으로 분류한 누락
- 보고서 footnote 정정 완료(`incident_improvement_20260421_session86.md` §3.5)
- γ 분류 폐기. 후속 보고서 작성 시 `tag` 필드도 분류 키로 사용

**[완료] 세션 시작훅 "최근 24h 신규" 집계 기준 검토 — TZ 버그 수정**
- 원인: `session_start_restore.sh:189` `date -d "-24 hours"`가 KST 로컬 시간(`2026-04-20T09:19`) 출력하는데 ledger ts는 UTC(`Z` 접미사). 사전순 비교 시 9시간 오프셋
- 수정: `date -u -d "-24 hours"` (UTF) + 주석 추가
- 실측 검증: awk 31건 → 97건(Python 동등 93건 ±5분 시차 수준 일치)
- A 분류 (단일 옵션 추가, 흐름 변경 없음)

**[완료] smoke_test 선행 2 FAIL 해소 (세션80부터 잔존)**
- FAIL 1 (README 훅 개수): smoke grep `'[0-9]+개 스크립트'` → `'[0-9]+개 (스크립트|등록)'`로 패턴 확장. README 의미 변경 없이 grep만 유연화
- FAIL 2 (classify_feedback --validate): 글로벌 메모리 4개 파일에 `enforcement: promptable` 태그 추가
  - `feedback_harness_label_required.md` (frontmatter 신규)
  - `feedback_share_gate_hook.md` (frontmatter 신규)
  - `feedback_structural_change_auto_three_way.md` (enforcement 자동 추가)
  - `feedback_threeway_share_both_required.md` (enforcement 자동 추가)
- smoke_test 결과: **212/212 PASS, 0 FAIL** (세션86 0이 됨)

**[이월 지속] β안-C 실제 구현** — 사용자 명시 승인 + API 키·예산 필요 (세션85 합의)

**[이월 지속] A안-2 실증** — 자연 발생 A 분류 의제 대기

**[이월 지속] Phase 2-C 재평가** — 2026-04-27 전후, `step5_final_verification_path_regression.md` 체크리스트

---

## 세션85 (2026-04-20, 이월 4건 처리 + β안-C [3way] 만장일치)

**[완료] TASKS.md 세션82~80 블록 아카이브** (96줄 감축, 770→674줄)
- 아카이브: `98_아카이브/tasks_archive_20260420_session85.md` (세션82~80 블록 100~195행 이관)
- 백업: `90_공통기준/업무관리/TASKS.md.bak_20260420_session85`
- 임계 상태: WARN(400) 초과 지속, STRONG(800) 미도달

**[완료] incident_ledger 실측 집계 + /auto-fix 일괄 적용 부적합 판정**
- 보고서: `90_공통기준/업무관리/incident_audit_20260420_session85.md`
- 실측: 총 1,197건 / resolved:false 1,005 / false_positive:true 45 / 실질 미해결 960
- 상위 5종(658건/68%) 전부 정책 gate 정상 차단 기록 (코드 버그 아님)
  1. evidence_gate map_scope.req 246
  2. commit_gate final_check --fast FAIL 159
  3. evidence_gate skill_read.req 89
  4. navigate_gate CLAUDE.md 미읽기 74
  5. evidence_gate tasks_handoff.req 65
- 판정: `/auto-fix` 일괄 적용 부적합. 근본 개선 방향 이월(evidence_gate self-throttle 확장 실측, completion_gate 소프트 블록 재검토)

**[완료] β안 3자 토론 Round 1 — β안-C 만장일치 채택 [3way]**
- 로그: `90_공통기준/토론모드/logs/debate_20260420_190020_beta_3way/` (agenda, round1_gpt/gemini/cross_verification/claude_synthesis/final)
- pass_ratio 1.0 (6-2·6-4 양측 동의 + 6-5 양측 동의)
- 독립의견 유지 검증: 쟁점 3 리스크 순위 GPT b>a>c / Gemini c>a>b 역순 산출 + Gemini 단독 "로그 브릿지 파이프라인" 신규 제안 → Claude 종합 통합 → 양측 동의
- 합의 내용: `[NEVER] API 호출` 조항의 **유일 예외** 신설 — Step 6-2/6-4 단발 교차 검증만 API 병렬 허용
- 규정 실물 반영 (본 세션):
  1. `90_공통기준/토론모드/CLAUDE.md` 금지사항 섹션 개정 + "β안-C 예외" 신규 섹션 (7개 필수 조건 + 확대 금지 [NEVER])
  2. `90_공통기준/토론모드/debate-mode/SKILL.md` Step 6-2/6-4 β안-C 섹션 신설 (API 전제 5개 + 로그 브릿지 JSON 스키마 + 실행 모드 분기 + [NEVER] 6개)
- **[이월·세션86+] 실제 구현**: `openai_debate.py` 리팩터 + Gemini API 클라이언트 신설 + smoke_test 신규 섹션(5건 이상) + 2주 관찰 기간

**[완료] A안-2 실증 판정**
- β안 의제는 B 분류(규정 개정 포함 프로토콜 변경) → `skip_65` 조건 C 불충족 → 자연 테스트 적용 안 됨
- critic-reviewer WARN(세션84 "실증 이월" 단서) **이월 지속**
- 다음 A 분류 의제 발생 시 재시도

---

## 세션84 (2026-04-20, 토론모드 진입 병목 감축 [3way] + 사용자 지시 예외 선례)

**[완료] D안 — 스킬 진입 세션캐시 (gpt-send/gemini-send 2회차 1-A/1-B 스킵)**
- 커밋: `ed0ba225`
- 사용자 실시간 불만 "스킬 사용하면 바로 웹 열어서 접속 해야 되는대 너무 느려" 대응
- 변경: `session_start_restore.sh`(*_skill_entry.ok 세션 시작 시 삭제), `gpt-send.md`·`gemini-send.md`(1-Z 캐시 체크 + 1-D 기록)
- 실측 PASS: 진입 tool 호출 7회 → 3회 (57% 감축), "수신 확인" 응답 정상 수령
- 사용자 지시 예외 적용 (3자 토론 중단 후 직접 구현)
- 토론 중단 로그: `90_공통기준/토론모드/logs/debate_20260420_163810_3way/abort.md`

**[완료] A안-1 — 자동 승격 트리거 A/B 분류 합리화 + 사용자 지시 예외 조항 신설**
- 커밋: `35a9ae32`
- 변경: `90_공통기준/토론모드/CLAUDE.md` "자동 승격 트리거" 섹션 개정
  - B 엄격화: "실행 흐름·판정 분기·차단 정책이 바뀌는 경우" 한정. 로그·timing·주석 추가 제외
  - A 확장: 훅 내 로그·timing 추가, 스킬 md 주석 추가, 사용자 명시 지시 예외 작업
  - 사용자 지시 예외 조항: 세션 내 사용자가 3자 승격 중단·거부하고 직접 구현 지시한 경우 1건 한정 B→A 강등. 커밋에 "사용자 지시 예외" + 중단 로그 링크 필수. 범위 확대 금지
  - [NEVER] 강화: 예외 외 B→A 강등 금지
- 메모리 `feedback_structural_change_auto_three_way.md` 동기화

**[완료] A안-2 — 3자 토론 6-5 양측 재검증 조건부 생략 규정 신설 [3way]**
- 커밋: `a37fd0fc` (3자 pass_ratio=1.0 만장일치)
- 변경: `90_공통기준/토론모드/debate-mode/SKILL.md` Step 3-W에 "6-5 조건부 생략" 섹션 신설 + JSON 스키마 4필드 확장 (`skip_65`, `skip_65_reason`, `claude_delta`, `issue_class`)
- 합의 조건: A(양측 무단서 동의) + B(Claude 순수 축약, `claude_delta="none"`) + C(A 분류만) + 시스템 제약(`round_count === 1` 하드제약)
- Gemini 보강 수용: ①`current_round === 1` 하드제약(수용), ②조건 통폐합(부분 수용 — A/B/C 3조건 유지, 의제 성격 C 분리로 프로토콜 변경 우회 차단)
- critic-reviewer 판정: WARN (독립 반론 부재 + "실증됨" 양측 합의 대체, Step 5 진행 허용 + 실증 이월)
- GPT 최종: 조건부 통과 (skip_65 실증 이월) / Gemini 최종: 통과 (SKILL.md 실물 확인 후)
- 로그: `90_공통기준/토론모드/logs/debate_20260420_171419_3way/`

**[이월] A안-2 실증** — 실제 A 분류 의제 발생 시 skip_65 발동 안전성 자연 테스트. critic-reviewer WARN 단서 해소 조건.

**[이월] β안** — 토론 내부 단발 검증 단계(6-2, 6-4) API 전환. 세션67 [NEVER] API 금지 규정 재검토 필요. 3자 토론 필수 (B 분류). 기대 효과: 라운드당 진입 절반 추가 감축.

**[이월] TASKS.md 감축** — 734줄 강경고 초과 지속. 세션80~82 블록 아카이브 고려 (세션83 감축 규모 참조).

---

## 세션83 (2026-04-20, evidence_gate 333건 원인 3자 API 예외 토론 [3way])

**[완료] 안건 B — 2026-04-19 evidence_missing 165건 집중 발화 audit_log 상세 분석**
- 산출: `90_공통기준/업무관리/evidence_gate_20260419_analysis.md`
- 7일 332건 (evidence_gate 272 + skill_instruction_gate 56 + instruction_not_read 4), 04-19 165건(49.7%)
- 04-19 01:06~01:53 KST 47분간 42건 단일 세션 commit/push 루프
- fingerprint 상위 3종 180/272 = 66% 집중, resolved:false 100%

**[완료] 안건 C — gpt-read/gpt-send thinking 확장추론 대응 ([3way] API 예외 토론)**
- 사용 모델: GPT-5.2 + Gemini 3.1-pro-preview (2자 API 교차 검증, Claude 독립 종합)
- Q1 slug 탐지: `slug.toLowerCase().includes('thinking'|'reasoning')` — GPT-5.2 allowlist 우려 부분 반영, Gemini 유연성 채택
- Q2 polling: isExtended=true 시 3/5/8/15초 반복, 300초 이후 30초, 최대 600초
- Q3 종료 판정: 블록 안정 3회 연속 동일 (stop-button 단독 판정 금지). 네트워크 idle(GPT-5.2 B안)은 MCP 불안정으로 미채택
- 수정: `.claude/commands/gpt-read.md` 2-a 확장, `.claude/commands/gpt-send.md` 4단계 보완
- smoke_test 섹션 49 신설 5/5 PASS
- 로그: `90_공통기준/토론모드/logs/debate_20260420_143000_api_exception/c_round1_summary.md`

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

**[완료] 안건 E — TASKS.md 감축** (924→724줄)
- 이관: 세션71~68 블록(718~924행) → `98_아카이브/tasks_archive_20260420_session83.md` (207줄)
- 백업: `90_공통기준/업무관리/TASKS.md.bak_20260420_session83`
- STRONG 임계(800줄) 완화. token_threshold_check 경고 해소

**[완료] 안건 D — 영문/특수문자/한글 경로 3종 회귀 테스트 체크리스트 고정**
- 신설: `90_공통기준/토론모드/step5_final_verification_path_regression.md`
- 세션82 GPT A 제안 반영. Phase 2-C 승격 전 필수 검증 3케이스 고정
- 합격 기준·실행 절차·변경 이력 포함

**[이월·세션84+] 안건 δ — skill_instruction_gate 36건 별건 분석** (본 토론 합의로 분리)

### 세션83 주의사항
- OpenAI API 키 `claude-code-debate-20260420`을 2026-04-20 14:22 KST 발급. 토론 종료 후 revoke 권장
- 토론모드 CLAUDE.md `[NEVER] API 호출` 규정은 다음 세션부터 원복 (이번 세션만 예외)

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


---

## 이전 세션 아카이브

- **세션68~70**: `98_아카이브/tasks_archive_20260420.md` (세션80 이관)
- **세션68~71**: `98_아카이브/tasks_archive_20260420_session83.md` (세션83 2차 이관)
