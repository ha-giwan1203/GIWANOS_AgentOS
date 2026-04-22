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

최종 업데이트: 2026-04-22 KST — 세션93 (Hook 시스템 2차 진단 + 개선 계획 수립 + 1주차 1번 착수)

---

## 세션93 (2026-04-22) — Hook 시스템 개선 (2자 토론 합의 plan.md 1주차 1번)

**[완료] 2차 진단 + 2자 토론 + 개선 계획 plan.md 작성**
- 2차 진단: GPT 2차 정밀진단 수령 → Claude 독립 검증 11/11 실증 + 등급 재조정 2건 제안
- 토론: 2자(Claude × GPT) 2라운드. 채택 11 / 보류 3 (해소 2, 잔존 1) / 버림 0
- 결론: "전면 재설계 대신 evidence 축 coverage 축소 + 남는 핵심 3종 contract형 재설계 하이브리드"
- 로그: `90_공통기준/토론모드/logs/debate_20260422_150445/plan.md` (1주차/2주차 + 검증 기준 + 롤백 조건)

**[완료] 1주차 1번 — hook_registry 격하 (Single Source of Truth 확정)**
- 변경 파일 (4개):
  - `.claude/scripts/hook_registry.sh` 상단 주석 [LEGACY / DEPRECATED] 표기 + 대체 경로 안내
  - `.claude/hooks/final_check.sh:139-149` `--fix` 경로 자동 sync 중단, list_active_hooks 기준 수동 갱신 안내로 전환
  - `.claude/hooks/README.md:6-12, 155-156` Single Source (list_active_hooks) 명시 + 보조 스크립트 표에 list_active_hooks 추가 + hook_registry legacy 표기
  - `90_공통기준/업무관리/STATUS.md:19` hooks 체계 기준축을 list_active_hooks로 명시
- 검증:
  - `list_active_hooks --count` = 31 (PreCompact 1 / SessionStart 1 / UserPromptSubmit 1 / PreToolUse 16 / PostToolUse 7 / Notification 1 / Stop 4)
  - `final_check --fast` 31/31/31 일치, exit 0
  - `smoke_fast` 11/11 ALL PASS
  - `doctor_lite` OK
- 소요: 약 30분

**[예정] 1주차 2번 — selfcheck 24h 정확 집계** (plan.md 1주차 2번)
**[예정] 1주차 3번 — doctor_lite python/python3 fallback** (plan.md 1주차 3번)
**[예정] 1주차 4번 — evidence coverage 축소** (plan.md 1주차 4번, 본 수술)
**[예정] 2주차 5~7번** (1주차 4번 + 1주 관찰 데이터 수령 후)

---

## 세션92 (2026-04-22) — Plan 잔여 안건 마무리 (IV-5 · IV-4 마무리 · V-7)

**[완료] 단계 IV 완결 + V-7 Notion parity + VIII 관찰 지표 기록**
- 계획 파일: `C:/Users/User/.claude/plans/staged-sprouting-perlis.md` (묶음 A/B/C)

**[완료] 묶음 A — Self-X Layer 1/4 원본 archive 이동**
- IV-5: `90_공통기준/invariants.yaml` → `98_아카이브/session91_glimmering/invariants_~session89.yaml`
- IV-4 마무리: `diagnose.py` / `quota_diagnose.py` / `last_diagnosis.json` → `98_아카이브/session91_glimmering/self_state/`
- 세션91 VII-2 staging 잔여(`circuit_breaker.json` / `meta.json` 삭제) 반영
- `DISPOSITION.md` 갱신: 완료 상태 표기 + V-2 드리프트 감지 경로 교환(render_hooks_readme.sh 단일화) 명시
- 검증: smoke_fast 11/11 ALL PASS / selfcheck "archive 상태" 정상 출력

**[완료] 묶음 B — V-7 Notion projection parity (코드 차원)**
- `notion_sync.py` 수정:
  - `_build_status_blocks` System Health 블록을 `summary.txt` 단일 경로로 단순화 (last_diagnosis.json fallback 제거)
  - Circuit Breaker 블록(L1141~1158) 전체 제거
  - Self-Recovery 블록 + `_recent_auto_recovery` 헬퍼 함수 제거
- grep 결과: `Self-X | Circuit Breaker | circuit_breaker | auto_recovery | Self-Recovery | quota_snapshot` 0건 (코드)
- `notion_snapshot.json` 재생성 — offline 경로(`generate_snapshot` + `write_snapshot_json` 직접 호출)
- 검증: python 구문 OK, hooks_active=31 유지, 렌더 블록 Self-X 현재 서술 0건
- 네트워크 push(`--manual-sync`)는 다음 `/finish` 또는 사용자 수동 트리거 시점에 자동 반영 예정

**[완료] 묶음 C — 단계 VIII 관찰 지표 기록 + 최종 정리**
- 지표 #2 smoke_fast: **11/11 ALL PASS** (2026-04-22 14:15 KST)
- 지표 #3 incident 신규 24h: **0건** (총 1226 / 해결 679 / 미해결 547 — 세션91 대비 변화 없음)
- 지표 #4 재도입 방지 grep: active 경로 **1건(의미상 0건)**
  - `.claude/hooks/hook_common.sh` `circuit_breaker_tripped()` + `commit_gate.sh` L86 호출부 + `smoke_test.sh` 해당 함수 capability 체크 3종은 **이름만 겹치는 incident_ledger 기반 advisory 함수** — Self-X Layer 4 런타임과 무관. archive 대상 아님.
  - 기타 매치: `migration_note_20260422.md`, `DESIGN_PRINCIPLES.md`, `DISPOSITION.md`, `session_start_restore.sh` historical 주석, `_archive/` 내부 = 전부 historical 서술. 재도입 아님.
- 지표 #5 Notion projection parity: Self-X 현재 서술 블록 **0건** (묶음 B에서 달성, 네트워크 push는 다음 /finish에 자동 반영)
- 지표 #1/#6 (체감 레이턴시 / archive 파일 30일 내 재생성): 세션간 유지형 지표 — 30일(2026-05-22) 만료 시점 재평가

**세션92 최종 커밋 3건**
| 커밋 | 단계 | 요약 |
|------|------|------|
| e539b380 | IV-5 + IV-4 마무리 | Self-X Layer 1/4 원본 5건 archive 이동 + DISPOSITION 갱신 |
| 60f76c9e | V-7 | notion_sync.py Self-X/Circuit Breaker 블록 제거 + snapshot 재생성 |
| (이번 커밋) | VIII | 단계 VIII 관찰 지표 기록 + 세션92 완결 |

**단계 VIII 관찰 기간**: 2026-04-22 ~ 2026-05-22 (30일 TTL). 만료 시점 재평가.

**[GPT 판정 PASS]** 2026-04-22 세션92 share-result (gpt-5-4-thinking)
- verdict: PASS / 3 item 전부 라벨=실증됨, 판정=동의 / 추가제안 없음
- 하네스: 채택 3 / 보류 0 / 버림 0

**[세션92 /finish 종료]** 2026-04-22 14:47 KST
- Notion `--manual-sync` 실행 성공 (Self-X/Circuit Breaker 서술 제거 확정)
- finish_state.json: terminal_state=done, final_sha=a1a81496
- 4커밋 전부 origin/main 반영 (`f2510ceb..a1a81496`)

---

## 세션91 (2026-04-22) — Plan 단계 III 2자 토론 + 구현 (게이트 3종 재절단)

**[완료] 2자 토론 4라운드 — 단계 III 설계 합의**
- 로그: `90_공통기준/토론모드/logs/debate_20260422_stage3_2way/` (round1~4 + SUMMARY.md)
- Round 1: Claude 독립 점검 5의제 제시 → GPT 5의제 전부 채택 (단 의제 1/4/5 Claude 초안 수정 요구)
- Round 2: 합의 확정안 → GPT 조건부 통과 (D 커밋 standalone 1회 조건)
- Round 3: 조건 수용 + 종결 선언 → GPT 최종 통과
- Round 4: Step 4b critic-reviewer WARN 제기(의제 4 "실증됨" 라벨 과대 부여) → GPT 실측 근거로 critic 지적 기각 + 사유 문구 교체 합의
- 채택 누계: 11 / 보류 0 / 버림 0

**[완료] 단계 III 구현 — 4커밋 순차 완료**
- 커밋 A (1935efd8): `commit_gate.sh` L81-98 제거 + `final_check.sh` statusLine 제외 + README/STATUS 드리프트 동기화
- 커밋 B (96b14617): `evidence_stop_guard.sh` L63-70 제거 (latent completion branch 정리)
- 커밋 C (b5fe9ecb): `evidence_gate.sh` suppress 라벨 `suppress_reason=evidence_recent` 고정
- 커밋 D (d7ee12f8): `gate_boundary_check.sh` 신설 (standalone 3/3 ALL PASS, 오탐 0) + smoke_fast 11/11 편입
- 회귀: 각 커밋 smoke_fast ALL PASS + final_check --full FAIL 0

**[진행중] 단계 IV — 뿌리 축소 + 수동화**
- [완료] IV-1: health_check.sh SessionStart 등록 해제 (세션90에서 완료)
- [완료] IV-2: `.claude/self/selfcheck.sh` 신설 (smoke_fast + doctor_lite + diagnose + quota + incident 묶음)
- [완료] IV-4: `.claude/self/DISPOSITION.md` 신설 (10개 파일 처리 방침)
- [대기] IV-5: invariants.yaml archive — 단계 V-1/V-2 완료 후

**[완료] 단계 V — Single Source 전환**
- V-1: `.claude/hooks/list_active_hooks.sh` 신설 (settings 기반 자동 집계)
- V-2: `.claude/hooks/render_hooks_readme.sh` 신설 (README/STATUS 숫자 자동 갱신) + `invariants.yaml` settings_drift WAIVER 해제 (원본 블록 복원)
- V-3: CLAUDE.md 훅 수 수동 서술 삭제 (list_active_hooks.sh 참조로 교체)
- V-4/V-5: `protected_assets.yaml` Self-X 항목 제거 + quota/ttl 블록 제거 (원본 `98_아카이브/session91_glimmering/`)
- V-6: CLAUDE.md Self-X Layer 전면 삭제
- [대기] V-7: Notion projection parity — 다음 세션 (네트워크 필요 `notion_sync.py --manual-sync`)

**[완료] 단계 VI — 슬림화**
- VI-1: CLAUDE.md Self-X Layer 전문 삭제 → `.claude/self/DESIGN_PRINCIPLES.md` 신설
- VI-2: MEMORY.md Self-X keyword audit (결과 0건 — 감축 불필요)
- VI-4: TASKS.md 965 → 123 줄 (세션88 이하 `98_아카이브/session91_glimmering/TASKS_~session88.md`)
- VI-5: incident_ledger 30일+ resolved 0건 → archive 실행 없음

**[완료] 단계 VII — Dormant surface 제거**
- VII-1: Self-X 폐기 hook 5종 → `.claude/hooks/archive/` 이동 (circuit_breaker_check, health_check, health_summary_gate, quota_advisory, self_recovery_t1)
- VII-2: `.claude/self/` 런타임 상태 → `98_아카이브/session91_glimmering/self_state/` 이동 (circuit_breaker.json, meta.json, auto_recovery.jsonl)

**[진행중] 단계 VIII — 30일 TTL 관찰 시작 (2026-04-22 ~ 2026-05-22)**
- 6개 관찰 지표:
  1. 체감 레이턴시 (세션 시작 + 첫 응답)
  2. smoke_fast 10/10+ 유지
  3. incident 신규 0 (24h)
  4. 재도입 방지 grep: active 경로에서 `self-x / health_summary / circuit_breaker / auto_recovery / quota` 0건
  5. Notion projection parity (Self-X/Quota 0건)
  6. `.claude/self/` archive 파일 30일 내 재생성 여부

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

**활성 훅**: 36 → **31** (SessionStart 3→1 / UserPromptSubmit 2→1 / PostToolUse 8→7 / Stop 5→4) — 세션91에서 실측 31 정정 (세션90 "30" 표기는 오기, list_active_hooks.sh --count 기준)
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


---

## 이전 세션 (세션88 이하) — 아카이브

세션88 이하 전체 기록은 `98_아카이브/session91_glimmering/TASKS_~session88.md` 참조.
세션91 VI-4 (2026-04-22) 슬림화로 TASKS.md를 최근 3개 세션(91/90/89)만 유지한다.
