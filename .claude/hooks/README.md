# Hooks 운영 현황

> Phase 3 완료 — 36개 → 5개 압축 (Round 1+2 합의안 채택, 세션137).
> 31개 폐기본은 `98_아카이브/_deprecated_v1/hooks/` 보존.
> 합의 원본: `90_공통기준/토론모드/logs/debate_20260503_101125_3way/round2_consensus.md`

## Single Source of Truth

활성 hook 카운트:
- `bash .claude/hooks/list_active_hooks.sh --count`
- `bash .claude/hooks/list_active_hooks.sh --by-event`

`final_check.sh`는 이 기준 + settings.json(team+local union)을 따른다.

## 활성 Hook 5개 (settings.json 기준)

| 훅 | matcher | 역할 |
|---|---|---|
| `block_dangerous.sh` | PreToolUse / Bash | 위험 명령 차단 (rm -rf, sudo, chmod 777). deterministic 차단만. |
| `commit_gate.sh` | PreToolUse / Bash | final_check --fast 통과 후만 commit/push 허용. 자연어 가이드 금지. |
| `protect_files.sh` | PreToolUse / Write\|Edit\|MultiEdit | 보호 파일(원본 xlsx·기준 문서) 수정 차단. deterministic. |
| `session_start_restore.sh` | SessionStart | git status·최근 commit 5건·TASKS·HANDOFF 상단·incident N건 데이터만 출력. 자연어 조언 금지. |
| `completion_gate.sh` | Stop | 통과/실패 + 누락 staged file만 보고. "반성하라"·"다음엔 이렇게 하라" 메시지 금지. |

## 핵심 운영 원칙 (Round 1+2 합의)

1. **출력의 건조함** — 도구는 상태와 데이터만 말함. 자연어 가이드 금지.
2. **결정론적 도구·코드만** — 행동 교정 명제 hook 추가 금지 (Round 2 의제2).
3. **행동 교정 메타 0** — `instruction_read_gate` / `r1r5_plan_check` / `permissions_sanity` / `skill_drift_check` / `risk_profile_prompt` / `skill_instruction_gate` 같은 카테고리 D는 영구 archive.

## 보조 파일 (settings.json 미등록, 라이브러리·헬퍼)

표가 아닌 목록 형식 (final_check 카운트는 첫 테이블 5행만 = 활성 hook 5개):

- `hook_common.sh` — 공통 함수 라이브러리 (등급 wrapper / fingerprint / suppress)
- `list_active_hooks.sh` — settings.json 기준 활성 hook 카운트 (final_check가 SSoT로 사용)
- `incident_repair.py` — session_start_restore가 호출하는 incident 분석 helper
- `record_incident.py` — gate hook이 차단 시 incident 적재
- `json_helper.py` — settings 파싱·hook 카운트 helper (Python 통일 fallback)
- `final_check.sh` — commit_gate가 호출하는 자체검증 (TASKS/HANDOFF/STATUS 동기화 + smoke_fast)
- `smoke_fast.sh` / `smoke_test.sh` — regression-only smoke + capability 포함 전체
- `doctor_lite.sh` — 가벼운 헬스체크 (session_start_restore 출력)
- `render_hooks_readme.sh` — 본 README 자동 갱신 helper (legacy, Phase 3 후 수동 운영)
- `gate_boundary_check.sh` / `nightly_capability_check.sh` / `pruning_observe.sh` / `share_gate.sh` / `domain_status_sync.sh` / `e2e_test.sh` / `statusline.sh` / `token_threshold_check.sh` / `incident_review.py` / `classify_feedback.py` — 보조 도구 (settings 미등록, 수동 호출 또는 schtasks)

## archive

- `_archive/` / `archive/` — 이전 세션에서 폐기된 hook (legacy)
- `98_아카이브/_deprecated_v1/hooks/` — Phase 3에서 폐기된 31개 (세션137)

## 롤백

```bash
# Phase 3 이전으로 복원
git reset --hard stable-before-reset
git push --force-with-lease origin main  # 사용자 명시 발화 시만
```

또는 settings.json만 복원:
```bash
git show stable-before-reset:.claude/settings.json > .claude/settings.json
```
