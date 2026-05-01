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
#
# 세션134 Phase 1 (P0 plan v2, 2026-05-01):
#   - final_check --fast 출력(stdout/stderr) tempfile 캡처 → 실패 원인 분류 → 처방형 메시지 출력
#   - dedupe: session_key + source_file + failure_signature 60분 윈도우
#     · 동일 signature 60분 내 반복 → incident_ledger 미기록, hook_log/stderr만 누적
#     · 60분 초과 또는 신규 signature → 기존대로 incident_ledger 기록 + 캐시 갱신
#   - final_check.sh / completion_gate.sh / write_marker.sh / settings.json 무수정
#   - 자동 commit/push 성공 경로 변경 없음 (final_check PASS 시 기존 line 그대로)

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
    # 세션134 Phase 1: stdout/stderr 캡처해서 실패 원인 분류·처방 출력 (final_check.sh 자체는 무수정)
    FC_OUT=$(mktemp 2>/dev/null) || FC_OUT="/tmp/auto_commit_fc_$$.out"
    FC_ERR=$(mktemp 2>/dev/null) || FC_ERR="/tmp/auto_commit_fc_$$.err"
    trap 'rm -f "$FC_OUT" "$FC_ERR" 2>/dev/null' EXIT

    bash .claude/hooks/final_check.sh --fast >"$FC_OUT" 2>"$FC_ERR"
    FC_EXIT=$?

    if [ $FC_EXIT -ne 0 ]; then
        # 세션105 Q1 기타안 Step 2: advisory 경고 문구 강화
        # - 이전 60분 내 동일 원인 반복 건수 집계
        # - AUTO 대상 파일 목록 표시 (미동기화 파일 가시성)
        # incident_ledger에서 최근 60분 completion_before_state_sync 건수
        RECENT_WINDOW_MIN=60
        RECENT_COUNT=0
        if [ -f ".claude/incident_ledger.jsonl" ]; then
            # epoch 현재 시간
            NOW_EPOCH=$(date -u +%s 2>/dev/null || echo 0)
            CUTOFF_EPOCH=$((NOW_EPOCH - RECENT_WINDOW_MIN * 60))
            RECENT_COUNT=$(grep '"hook":"auto_commit_state".*"classification_reason":"completion_before_state_sync"\|"hook": "auto_commit_state".*"classification_reason": "completion_before_state_sync"' \
                .claude/incident_ledger.jsonl 2>/dev/null | \
                awk -v cutoff="$CUTOFF_EPOCH" '{
                    match($0, /"ts":"([^"]+)"/, a)
                    if (a[1]) {
                        cmd = "date -d \"" a[1] "\" -u +%s 2>/dev/null"
                        cmd | getline ts_epoch
                        close(cmd)
                        if (ts_epoch+0 >= cutoff+0) count++
                    }
                }
                END { print count+0 }')
            [ -z "$RECENT_COUNT" ] && RECENT_COUNT=0
        fi

        # ── 세션134 Phase 1 신설: 실패 원인 분류 (정규식 매핑 7종 + fallback) ──
        FC_COMBINED="$(cat "$FC_OUT" "$FC_ERR" 2>/dev/null)"
        SIG_CODES=""
        PRESCRIPTIONS=""

        _add_prescription() {
            local code="$1"
            local msg="$2"
            SIG_CODES="${SIG_CODES}${SIG_CODES:+,}${code}"
            PRESCRIPTIONS="${PRESCRIPTIONS}      [${code}] ${msg}
"
        }

        if echo "$FC_COMBINED" | grep -qE '\[FAIL\] STATUS\(세션[0-9]+\) < TASKS\(세션[0-9]+\)'; then
            _add_prescription "session_drift" "STATUS 세션 < TASKS 세션 → bash .claude/hooks/final_check.sh --fast --fix"
        fi
        if echo "$FC_COMBINED" | grep -qE '\[FAIL\] STATUS\([0-9-]+\) < TASKS\([0-9-]+\)'; then
            _add_prescription "meta_drift" "STATUS 날짜 < TASKS 날짜 → bash .claude/hooks/final_check.sh --fast --fix"
        fi
        for fname in TASKS HANDOFF STATUS; do
            if echo "$FC_COMBINED" | grep -qE "\[FAIL\] ${fname}\.md — write_marker 이후 미갱신"; then
                _add_prescription "marker_stale_${fname}" "${fname}.md 세션 블록에 현 세션 작업 결과 1~2줄 추가 후 재시도"
            fi
        done
        if echo "$FC_COMBINED" | grep -qE '\[FAIL\] hook_log\.txt 직접 참조 잔존'; then
            _add_prescription "legacy_log_ref" "세션93 마이그레이션 잔존 — hook 코드 점검 (advisory)"
        fi
        if echo "$FC_COMBINED" | grep -qE '\[FAIL\] settings 등록 훅 파일 누락'; then
            _add_prescription "missing_hook_file" "settings.json 등록 hook 실파일 부재 — settings/hook 파일 점검"
        fi
        if echo "$FC_COMBINED" | grep -qE '\[FAIL\] STATUS\([0-9]+\) ≠ settings\([0-9]+\)'; then
            _add_prescription "status_count_drift" "STATUS.md hook 카운트 동적 참조로 갱신 (list_active_hooks --count 참조)"
        fi
        if echo "$FC_COMBINED" | grep -qE '\[FAIL\] README\([0-9]+\) ≠ settings\([0-9]+\)'; then
            _add_prescription "readme_count_drift" "README.md 활성 hook 표 갱신 (list_active_hooks --by-event 참조)"
        fi
        # fallback: 분류 안 된 FAIL 라인 잔존
        TOTAL_FAILS=$(echo "$FC_COMBINED" | grep -cE '\[FAIL\]' 2>/dev/null)
        [ -z "$TOTAL_FAILS" ] && TOTAL_FAILS=0
        CLASSIFIED=$(echo "$SIG_CODES" | tr ',' '\n' | grep -v '^$' | wc -l | tr -d ' ' 2>/dev/null)
        [ -z "$CLASSIFIED" ] && CLASSIFIED=0
        if [ "$TOTAL_FAILS" -gt "$CLASSIFIED" ] 2>/dev/null && [ "$CLASSIFIED" -gt 0 ] 2>/dev/null; then
            _add_prescription "unclassified" "분류되지 않은 FAIL 항목 잔존 — bash .claude/hooks/final_check.sh --fast 직접 확인"
        elif [ "$CLASSIFIED" -eq 0 ] 2>/dev/null && [ "$TOTAL_FAILS" -gt 0 ] 2>/dev/null; then
            _add_prescription "unclassified" "분류되지 않은 FAIL 항목 ${TOTAL_FAILS}건 — bash .claude/hooks/final_check.sh --fast 직접 확인"
        fi

        # ── 세션134 Phase 1 신설: dedupe 키 산출 ──
        SESSION_KEY_VAL=$(session_key 2>/dev/null)
        [ -z "$SESSION_KEY_VAL" ] && SESSION_KEY_VAL="unknown"
        SOURCE_FILE_VAL="unknown"
        if [ -f "90_공통기준/agent-control/state/write_marker.json" ]; then
            SOURCE_FILE_VAL=$(safe_json_get "source_file" < "90_공통기준/agent-control/state/write_marker.json" 2>/dev/null)
            [ -z "$SOURCE_FILE_VAL" ] && SOURCE_FILE_VAL="unknown"
        fi
        # failure_signature: SIG_CODES 정렬·중복제거
        FAILURE_SIG=$(echo "$SIG_CODES" | tr ',' '\n' | grep -v '^$' | sort -u | paste -sd, - 2>/dev/null)
        [ -z "$FAILURE_SIG" ] && FAILURE_SIG="empty"
        DEDUPE_KEY=$(printf '%s|%s|%s' "$SESSION_KEY_VAL" "$SOURCE_FILE_VAL" "$FAILURE_SIG" | sha1sum 2>/dev/null | cut -c1-8)
        [ -z "$DEDUPE_KEY" ] && DEDUPE_KEY="nokey"

        DEDUPE_DIR=".claude/state"
        DEDUPE_CACHE="${DEDUPE_DIR}/auto_commit_dedupe_${DEDUPE_KEY}.txt"
        NOW_EPOCH_DEDUPE=$(date -u +%s 2>/dev/null || echo 0)
        DEDUPE_RECENT=false
        REPEAT_N=1
        if [ -f "$DEDUPE_CACHE" ]; then
            CACHE_EPOCH=$(stat -c '%Y' "$DEDUPE_CACHE" 2>/dev/null)
            [ -z "$CACHE_EPOCH" ] && CACHE_EPOCH=$(stat -f '%m' "$DEDUPE_CACHE" 2>/dev/null)
            [ -z "$CACHE_EPOCH" ] && CACHE_EPOCH=0
            AGE=$((NOW_EPOCH_DEDUPE - CACHE_EPOCH))
            if [ "$AGE" -lt 3600 ] 2>/dev/null && [ "$AGE" -ge 0 ] 2>/dev/null; then
                DEDUPE_RECENT=true
                # 반복 카운트 증가
                CURRENT_COUNT=$(cat "$DEDUPE_CACHE.count" 2>/dev/null || echo 1)
                REPEAT_N=$((CURRENT_COUNT + 1))
                echo "$REPEAT_N" > "$DEDUPE_CACHE.count" 2>/dev/null
            fi
        fi

        # ── 기존 advisory 출력 (보존) + 처방 메시지 추가 ──
        echo "" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "⛔  [auto_commit_state] final_check --fast 실패" >&2
        echo "    → 자동 커밋/푸시 차단 (AUTO 파일 ${#AUTO_FILES[@]}건)" >&2
        echo "" >&2
        echo "    미동기화 대상 AUTO 파일:" >&2
        for f in "${AUTO_FILES[@]}"; do echo "      - $f" >&2; done

        # 세션134 Phase 1: 처방 메시지 출력
        if [ -n "$PRESCRIPTIONS" ]; then
            echo "" >&2
            echo "    ── 처방 (final_check FAIL 분류) ──" >&2
            printf '%s' "$PRESCRIPTIONS" >&2
        fi

        if [ "$RECENT_COUNT" -ge 3 ] 2>/dev/null; then
            echo "" >&2
            echo "    ⚠ 최근 ${RECENT_WINDOW_MIN}분 내 동일 원인(completion_before_state_sync) 중복: ${RECENT_COUNT}건" >&2
            echo "      → TASKS/HANDOFF/STATUS 실제 내용 갱신 후 재시도 필요" >&2
            echo "      → 세션105 재점화 조건 1 접근 (7일 3건 이상 AND final_check 실패 2건 이상)" >&2
        fi
        echo "" >&2
        echo "    → /finish 또는 수동 git commit 후 git push 필요" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

        # ── 세션134 Phase 1: dedupe 적용 ──
        # incident 기록 (세션102 [3way] 합의 — Q2 B안) — dedupe 미적용 시에만
        if [ "$DEDUPE_RECENT" = "true" ]; then
            echo "    [dedupe] 60분 내 동일 패턴 ${REPEAT_N}회째 (key=${DEDUPE_KEY}, sig=${FAILURE_SIG}) — incident_ledger 미기록 (hook_log/stderr만)" >&2
            hook_log "auto_commit_dedupe" "skip incident: signature=${FAILURE_SIG} key=${DEDUPE_KEY} session=${SESSION_KEY_VAL} repeat=${REPEAT_N}" 2>/dev/null || true
        else
            # 신규 signature 또는 60분 초과 → 기존대로 incident_ledger 기록 + 캐시 갱신
            hook_incident "hook_block" "auto_commit_state" "" \
                "final_check --fast 실패로 자동 commit/push 차단 (AUTO 파일 ${#AUTO_FILES[@]}건, recent_60m=${RECENT_COUNT})" \
                "\"classification_reason\":\"completion_before_state_sync\",\"recent_60m\":${RECENT_COUNT},\"failure_signature\":\"${FAILURE_SIG}\",\"dedupe_key\":\"${DEDUPE_KEY}\"" 2>/dev/null || true
            hook_log "auto_commit_blocked" "final_check fail — ${#AUTO_FILES[@]} files, recent_60m=${RECENT_COUNT}, sig=${FAILURE_SIG}, key=${DEDUPE_KEY}" 2>/dev/null || true
            # 캐시 갱신 (mtime 자동 갱신)
            mkdir -p "$DEDUPE_DIR" 2>/dev/null
            echo "$NOW_EPOCH_DEDUPE" > "$DEDUPE_CACHE" 2>/dev/null
            echo "1" > "$DEDUPE_CACHE.count" 2>/dev/null
        fi

        # stale 캐시 정리 — 개수 기준만(최신 50개 보존). 60분은 dedupe 판정 윈도우일 뿐, 정리 기준 아님
        if [ -d "$DEDUPE_DIR" ]; then
            ls -t "$DEDUPE_DIR"/auto_commit_dedupe_*.txt 2>/dev/null | tail -n +51 | while IFS= read -r stale; do
                [ -n "$stale" ] && rm -f "$stale" "${stale}.count" 2>/dev/null
            done
        fi

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
