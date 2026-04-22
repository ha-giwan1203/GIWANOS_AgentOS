#!/bin/bash
# Self-X Layer 1 — UserPromptSubmit health summary advisory + 컨텍스트 주입
# 출처: debate_20260421_133506_3way (M3 advisory + 보강 프롬프트 자동 주입)
# 등급: advisory (사용자 메시지 차단 없음, exit 0 강제. Phase 2-C에서 hard gate 검토)
# 정책: M3 보강 프롬프트 stderr 주입 / M4 단순 인사 면제 / Q-Range 프로젝트성 키워드 매칭 시만 강제
#
# 동작 (Q-Range 합의 정합): 프로젝트성 작업 키워드 감지 시만 리마인더 주입.
# 일반 대화·단순 인사는 면제. M1과 동일하게 stderr로 Claude 컨텍스트 주입.

set +e

source "$(dirname "$0")/hook_common.sh"
_HSG_START=$(hook_timing_start)

INPUT=$(cat)
PROMPT=$(printf '%s' "$INPUT" | safe_json_get "prompt" 2>/dev/null || echo "")

# M4: 단순 인사·확인 즉시 면제 (1차 필터)
SIMPLE_PATTERN='^(안녕|hi|hello|테스트|test|확인|ok|네$|예$|좋아|좋습니다|감사|고마워|뭐해|상태\?|reset|clear|/help|/status)'
if echo "$PROMPT" | head -1 | grep -qiE "$SIMPLE_PATTERN"; then
  hook_log "health_summary_gate" "exempt simple_greeting"
  hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
  exit 0
fi

# Q-Range (3way 합의): 프로젝트성 작업 키워드 매칭 시만 강제
# 미매칭이면 면제 (GPT 우려: "단순 질문에 진단 튀어나옴" 방지)
# 키워드 목록 출처: 90_공통기준/project_keywords.txt (세션88 분리)
# 파일 부재·읽기 실패 시 하드코딩 fallback 유지 (advisory hook 특성: exit 0 보장)
KEYWORDS_FILE="$PROJECT_ROOT/90_공통기준/project_keywords.txt"
PROJECT_KEYWORDS=""
if [ -r "$KEYWORDS_FILE" ]; then
  PROJECT_KEYWORDS=$(grep -vE '^\s*(#|$)' "$KEYWORDS_FILE" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
fi
if [ -z "$PROJECT_KEYWORDS" ]; then
  PROJECT_KEYWORDS='/finish|/debate-mode|/settlement|/share-result|/sync|/auto-fix|/self-audit|/daily|/line-batch|/production|/zdm|정산|라인배치|생산실적|MES|ERP|토론모드|자가진단|invariant|self-x|health|배포|런북|deploy'
fi
if ! echo "$PROMPT" | grep -qiE "$PROJECT_KEYWORDS"; then
  hook_log "health_summary_gate" "exempt non_project_msg"
  hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
  exit 0
fi

# 세션 첫 프로젝트성 메시지인지 확인
FIRST_MARKER="$PROJECT_ROOT/.claude/state/health_summary_first.ok"
if [ -f "$FIRST_MARKER" ]; then
  hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
  exit 0
fi

# 첫 프로젝트성 메시지: health summary advisory 리마인더 stderr 주입 (M1과 동일 채널)
SUMMARY_FILE="$PROJECT_ROOT/.claude/self/summary.txt"
if [ -f "$SUMMARY_FILE" ]; then
  SUMMARY=$(cat "$SUMMARY_FILE" | head -1)
  echo "" >&2
  echo "[health-summary-advisory] Claude 첫 응답에 다음 1줄 포함 권고:" >&2
  echo "  $SUMMARY" >&2
  echo "  (WARN/CRITICAL 시 자동 펼침. 상세: .claude/self/HEALTH.md)" >&2
  echo "" >&2
  hook_log "health_summary_gate" "reminder_injected summary=$SUMMARY"
fi

touch "$FIRST_MARKER"
hook_timing_end "health_summary_gate" "$_HSG_START" "advisory"
exit 0
