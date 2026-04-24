#!/usr/bin/env bash
# auto_commit_state.sh — 하이브리드 자동 커밋 (세션101 2026-04-24 신설, 세션102 hook_common 적용)
#
# 정책:
#   - 상태 문서(AUTO)는 세션 종료 시 자동 커밋+푸시
#   - 코드/스킬/설정(MANUAL)은 stderr 리마인더만, 사용자가 /finish 또는 수동 커밋
#
# AUTO 대상:
#   - */TASKS.md, */HANDOFF.md, */STATUS.md (루트 + 도메인)
#   - 90_공통기준/업무관리/notion_snapshot.json
#   - 90_공통기준/agent-control/state/finish_state.json
#   - 90_공통기준/agent-control/state/write_marker.json
#
# 등급: advisory (실패해도 세션 계속, exit 0 강제)
# 계측: hook_common.sh의 timing/incident/log 함수 사용 (세션102 [3way] 합의)

set +e
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

# hook_common.sh 로드 (timing/incident/log 함수)
if [ -f ".claude/hooks/hook_common.sh" ]; then
    # shellcheck source=/dev/null
    source .claude/hooks/hook_common.sh
fi
HOOK_START_TS=$(hook_timing_start 2>/dev/null || echo "")

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
[ "$BRANCH" = "main" ] || { echo "[auto_commit_state] main 브랜치만 동작 (현재: $BRANCH)" >&2; exit 0; }

# git status --porcelain 파싱 (한글 경로 그대로 출력)
CHANGED=$(git -c core.quotepath=false status --porcelain 2>/dev/null)
[ -z "$CHANGED" ] && exit 0

# AUTO 패턴 (정규식)
AUTO_PAT='(TASKS\.md|HANDOFF\.md|STATUS\.md|notion_snapshot\.json|finish_state\.json|write_marker\.json)$'

# 분류
AUTO_FILES=()
MANUAL_FILES=()
while IFS= read -r line; do
    # " M path" 또는 "?? path" 형태. 앞 3글자 건너뛰고 경로만
    path="${line:3}"
    # 따옴표 제거
    path="${path%\"}"
    path="${path#\"}"
    if echo "$path" | grep -qE "$AUTO_PAT"; then
        AUTO_FILES+=("$path")
    else
        MANUAL_FILES+=("$path")
    fi
done <<< "$CHANGED"

# MANUAL 리마인더 (stderr)
if [ ${#MANUAL_FILES[@]} -gt 0 ]; then
    echo "[auto_commit_state] ⚠ 수동 커밋 필요 파일 ${#MANUAL_FILES[@]}건:" >&2
    for f in "${MANUAL_FILES[@]}"; do echo "    - $f" >&2; done
    echo "    → /finish 실행 또는 수동 git commit 진행 권장" >&2
fi

# AUTO 자동 커밋+푸시
if [ ${#AUTO_FILES[@]} -gt 0 ]; then
    echo "[auto_commit_state] 상태문서 ${#AUTO_FILES[@]}건 자동 커밋 시도" >&2

    # 민감 패턴 스캔 (password/secret/key/token) — 있으면 중단
    for f in "${AUTO_FILES[@]}"; do
        if [ -f "$f" ] && grep -qiE '(password|secret|api[_-]?key|bearer\s+[a-z0-9])' "$f" 2>/dev/null; then
            echo "[auto_commit_state] ⛔ 민감 패턴 감지 ($f) — 자동 커밋 중단, 수동 검토 필요" >&2
            exit 0
        fi
    done

    git add "${AUTO_FILES[@]}" 2>/dev/null
    SESSION=$(grep -oE '세션[0-9]+' "90_공통기준/업무관리/TASKS.md" 2>/dev/null | head -1 | grep -oE '[0-9]+')
    [ -z "$SESSION" ] && SESSION="unknown"

    MSG="docs(state): 세션${SESSION} 상태문서 자동 동기화 [auto]

변경: ${#AUTO_FILES[@]}건
$(printf '  - %s\n' "${AUTO_FILES[@]}" | head -6)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

    # 커밋 전 자체검증 (GPT A-수정안, 3자 토론 2026-04-24 합의)
    # commit_gate는 PreToolUse Bash 매처 전용이라 Stop hook 내부 git 호출을 잡지 못함.
    # 대신 final_check.sh --fast로 교차검증만 수행.
    if ! bash .claude/hooks/final_check.sh --fast >/dev/null 2>&1; then
        echo "" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "⛔  [auto_commit_state] final_check --fast 실패" >&2
        echo "    → 자동 커밋/푸시 차단 (AUTO 파일 ${#AUTO_FILES[@]}건)" >&2
        echo "    → /finish 또는 수동 git commit 후 git push 필요" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        # incident 기록 (세션102 [3way] 합의 — Q2 B안)
        hook_incident "hook_block" "auto_commit_state" "" \
            "final_check --fast 실패로 자동 commit/push 차단 (AUTO 파일 ${#AUTO_FILES[@]}건)" \
            "\"classification_reason\":\"completion_before_state_sync\"" 2>/dev/null || true
        hook_log "auto_commit_blocked" "final_check fail — ${#AUTO_FILES[@]} files" 2>/dev/null || true
        hook_timing_end "auto_commit_state" "$HOOK_START_TS" "advisory_blocked" 2>/dev/null || true
        exit 0
    fi

    if git commit -m "$MSG" >&2 2>&1; then
        echo "[auto_commit_state] 커밋 완료 — push 시도" >&2
        if timeout 60 git push origin main >&2 2>&1; then
            echo "[auto_commit_state] ✅ push 완료" >&2
            hook_log "auto_commit_pushed" "${#AUTO_FILES[@]} files" 2>/dev/null || true
            hook_timing_end "auto_commit_state" "$HOOK_START_TS" "ok" 2>/dev/null || true
        else
            echo "[auto_commit_state] ⚠ push 실패 — 수동 재시도 필요 (git push origin main)" >&2
            hook_incident "hook_block" "auto_commit_state" "" \
                "git push 실패 (timeout 또는 네트워크) — ${#AUTO_FILES[@]} files staged" \
                "\"classification_reason\":\"pre_commit_check\"" 2>/dev/null || true
            hook_timing_end "auto_commit_state" "$HOOK_START_TS" "push_fail" 2>/dev/null || true
        fi
    else
        echo "[auto_commit_state] ⚠ 커밋 실패 — 상태문서 변경 없거나 hook 거부" >&2
        hook_log "auto_commit_failed" "git commit failed" 2>/dev/null || true
        hook_timing_end "auto_commit_state" "$HOOK_START_TS" "commit_fail" 2>/dev/null || true
    fi
else
    # AUTO 파일 없는 경우도 timing 기록 (정상 종료)
    hook_timing_end "auto_commit_state" "$HOOK_START_TS" "no_auto_files" 2>/dev/null || true
fi

exit 0
