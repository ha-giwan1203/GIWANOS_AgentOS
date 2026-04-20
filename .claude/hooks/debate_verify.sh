#!/bin/bash
# debate_verify — 3자 토론(3way) 산출물 커밋 시 3자 서명 기계적 강제 검증
# 세션68 Claude 오케스트레이션 누락 사고 재발 방지
# 2026-04-18 3자 토론 Round 2 (Claude 설계 주체)
#
# 훅 등급: Phase 1 advisory (설계상 gate, 실코드 advisory)
# Phase 1: 경고만 (stderr + exit 0) — 1주 운영 후 incident 0건이면 Phase 2 전환
# Phase 2: 차단 (exit 2) — incident_ledger "debate_verify" 태그 7일 연속 0건 달성 시 승격
#   현재(2026-04-19 세션72): incident 18건 잔존 → Phase 2 전환 **보류**. Phase 2-C에서 재평가.
# Phase 3: step5_final_verification.md 자동 생성 헬퍼
#
# Phase 2-B 진행 사항 (2026-04-19 세션72): timing 계측만 추가. exit 코드 정책 변경 없음.

set -u

source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true

_DV_START=$(hook_timing_start)

# Claude Code PreToolUse hook: stdin으로 JSON 전달 (tool_input 포함)
INPUT=$(cat)

# Bash 매처에만 반응
TOOL_NAME=$(printf '%s' "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
if [ "$TOOL_NAME" != "Bash" ]; then
  hook_timing_end "debate_verify" "$_DV_START" "skip_nonbash"
  exit 0
fi

COMMAND=$(printf '%s' "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# git commit 명령만 대상
case "$COMMAND" in
  *"git commit"*|*"git -C"*"commit"*) ;;
  *) hook_timing_end "debate_verify" "$_DV_START" "skip_noncommit"; exit 0 ;;
esac

# WIP 예외: [WIP 3way] 접두사 시 스킵
if echo "$COMMAND" | grep -qE '\[WIP 3way\]'; then
  hook_timing_end "debate_verify" "$_DV_START" "skip_wip"
  exit 0
fi

# 3way 감지: 커밋 메시지 또는 git diff 경로
IS_3WAY=0
if echo "$COMMAND" | grep -qE '\[3way\]|3way|debate_[0-9]{8}_[0-9]{6}_3way|3-way|3자[[:space:]]*토론'; then
  IS_3WAY=1
fi

# 보조 감지: staged diff에 debate_*_3way/ 경로 있는지
if [ "$IS_3WAY" -eq 0 ]; then
  STAGED=$(git -C "${PROJECT_ROOT:-.}" diff --cached --name-only 2>/dev/null || true)
  if echo "$STAGED" | grep -qE 'debate_[0-9]{8}_[0-9]{6}_3way/'; then
    IS_3WAY=1
  fi
fi

# 3way 아니면 통과
if [ "$IS_3WAY" -eq 0 ]; then
  hook_timing_end "debate_verify" "$_DV_START" "skip_non3way"
  exit 0
fi

ERRORS=()

# 최신 3way 로그 디렉토리 탐색
LOG_BASE="${PROJECT_ROOT:-.}/90_공통기준/토론모드/logs"
LATEST_3WAY=$(ls -dt "$LOG_BASE"/debate_*_3way 2>/dev/null | head -1)

if [ -z "$LATEST_3WAY" ]; then
  ERRORS+=("3way 로그 디렉토리 없음 — $LOG_BASE/debate_*_3way")
else
  RESULT="$LATEST_3WAY/result.json"
  STEP5="$LATEST_3WAY/step5_final_verification.md"

  # 1. result.json 존재 + JSON 유효
  # Windows Git Bash POSIX 경로(/c/Users/...)를 네이티브 Python3에 전달 시 os.path.exists
  # 오탐지 + 쉘 인라인 전개 중 locale/code page 경유 한글 경로 깨짐 이슈 해결.
  # cygpath + os.environ + <<'PY' quoted heredoc + Python 2차 정규화 조합으로 다중 방어.
  # 2026-04-20 3자 토론(Claude×GPT×Gemini) 합의안 반영.
  if [ ! -f "$RESULT" ]; then
    ERRORS+=("result.json 누락: $RESULT")
  else
    # 경로를 Windows 형식으로 사전 변환 (cygpath 우선 + 범용 sed fallback)
    RESULT_WIN=$(cygpath -w "$RESULT" 2>/dev/null || \
                 echo "$RESULT" | sed -E 's|^/([a-zA-Z])/|\1:/|')
    VALIDATE=$(RESULT_ENV="$RESULT_WIN" PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 <<'PY' 2>&1
import json, sys, os, re
path = os.environ['RESULT_ENV']
# Python 측 2차 안전망: POSIX /<letter>/ prefix 정규화 + normpath
path = re.sub(r'^/([a-zA-Z])/', r'\1:/', path)
path = os.path.normpath(path)
try:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
except Exception as e:
    print(f"JSON_ERROR:{e}"); sys.exit(1)

issues = []
turns = d.get("turns", [])
if not turns:
    issues.append("turns[] 비어있음")

req_keys = ["gpt_verifies_gemini", "gemini_verifies_gpt", "gpt_verifies_claude", "gemini_verifies_claude"]
enum_verdicts = {"동의", "이의", "검증 필요"}

for i, t in enumerate(turns):
    cv = t.get("cross_verification")
    if not cv:
        issues.append(f"turn[{i}] cross_verification 누락")
        continue
    for k in req_keys:
        v = cv.get(k)
        if not v:
            issues.append(f"turn[{i}].{k} 누락")
            continue
        verdict = v.get("verdict", "")
        reason = v.get("reason", "")
        if verdict not in enum_verdicts:
            issues.append(f"turn[{i}].{k}.verdict 비enum: '{verdict}'")
        if not reason.strip():
            issues.append(f"turn[{i}].{k}.reason 비어있음")
    pr = cv.get("pass_ratio_numeric", 0)
    if i == len(turns) - 1 and pr < 0.67:
        issues.append(f"최종 라운드 pass_ratio={pr} < 0.67")
    # round_count/max_rounds 일관성 (Round 2 양측 합의)
    rc = cv.get("round_count", 0)
    mr = cv.get("max_rounds", 3)
    if rc > mr:
        issues.append(f"turn[{i}] round_count={rc} > max_rounds={mr} — 합의 실패 판정 누락")
    if i == len(turns) - 1 and rc == mr and pr < 0.67:
        issues.append(f"turn[{i}] 최종 라운드(max_rounds 도달) + pass_ratio 미달 → consensus_failure.md 필요")

for x in issues:
    print(f"FIELD:{x}")
PY
)
    if echo "$VALIDATE" | grep -q "^JSON_ERROR:"; then
      ERRORS+=("result.json 파싱 실패: $(echo "$VALIDATE" | sed 's/^JSON_ERROR://')")
    fi
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      ERRORS+=("${line#FIELD:}")
    done < <(echo "$VALIDATE" | grep "^FIELD:")
  fi

  # 2. step5_final_verification.md 존재 + 양측 판정 섹션
  if [ ! -f "$STEP5" ]; then
    ERRORS+=("step5_final_verification.md 누락 — 3way Step 5 기록 필수")
  else
    if ! grep -qE '^##[[:space:]]+GPT[[:space:]]+최종[[:space:]]+판정' "$STEP5"; then
      ERRORS+=("step5에 'GPT 최종 판정' 섹션 누락")
    fi
    if ! grep -qE '^##[[:space:]]+Gemini[[:space:]]+최종[[:space:]]+판정' "$STEP5"; then
      ERRORS+=("step5에 'Gemini 최종 판정' 섹션 누락 — SKILL.md 5-3 위반")
    fi
    # 양측 판정 키워드 존재
    if ! grep -qE '\*\*(통과|조건부 통과|실패|통과 승격)\*\*' "$STEP5"; then
      ERRORS+=("step5에 판정 키워드(**통과/조건부 통과/실패/통과 승격**) 없음")
    fi
  fi
fi

# 결과 출력
if [ ${#ERRORS[@]} -eq 0 ]; then
  hook_timing_end "debate_verify" "$_DV_START" "pass"
  exit 0
fi

# Phase 1: 경고만
echo "[debate_verify] ⚠️ 3way 합의 서명 검증 실패 (${#ERRORS[@]}건) — Phase 1 경고 모드" >&2
for e in "${ERRORS[@]}"; do
  echo "  - $e" >&2
done
echo "[debate_verify] Phase 2 전환 시 커밋 차단됨. 현재는 경고만." >&2

# JSONL 로그 기록 (Round 2 양측 합의 — Phase 2 전환 기준 계측)
LEDGER="${PROJECT_ROOT:-.}/.claude/incident_ledger.jsonl"
if [ -w "$(dirname "$LEDGER")" ]; then
  TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || echo "")
  ISSUES_JSON=$(printf '%s\n' "${ERRORS[@]}" | PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 -c "import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()], ensure_ascii=False))" 2>/dev/null || echo "[]")
  echo "{\"ts\":\"$TS\",\"tag\":\"debate_verify\",\"phase\":1,\"count\":${#ERRORS[@]},\"issues\":$ISSUES_JSON,\"resolved\":false}" >> "$LEDGER"
fi

# Phase 1: 경고만, 차단 없음 (Phase 2-C 이후 exit 2 전환 예정 — incident 0건 조건)
hook_timing_end "debate_verify" "$_DV_START" "phase1_warn"
exit 0
