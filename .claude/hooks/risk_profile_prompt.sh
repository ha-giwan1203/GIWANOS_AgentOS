#!/bin/bash
# UserPromptSubmit — 현재 사용자 프롬프트 기준 req 생성
# 주의: 요청마다 req를 재생성한다. 이전 req 누적 금지.

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT="$(cat)"

SESSION_KEY="$(session_key)"
SESSION_DIR="$STATE_EVIDENCE/$SESSION_KEY"
REQ_DIR="$SESSION_DIR/requires"
PROOF_DIR="$SESSION_DIR/proofs"
START_FILE="$SESSION_DIR/.session_start"

mkdir -p "$REQ_DIR" "$PROOF_DIR"

# 세션 시작 스탬프 lazily 생성
if [ ! -f "$START_FILE" ]; then
  : > "$START_FILE"
fi

# 프롬프트마다 req 재생성
find "$REQ_DIR" -type f -name '*.req' -delete 2>/dev/null || true

TEXT="$(printf '%s' "$INPUT" | tr '\n' ' ' | sed 's/\\"/"/g')"
REQS=""

touch_req() {
  local name="$1"
  : > "$REQ_DIR/$name.req"
  REQS="${REQS}${REQS:+,}$name"
}

# 날짜/요일/ZDM
if echo "$TEXT" | grep -qiE '(ZDM|일상점검|daily[-_ ]inspection|점검표|요일|일요일|월요일|화요일|수요일|목요일|금요일|토요일|[0-9]{4}[./-][0-9]{1,2}[./-][0-9]{1,2}|[0-9]{1,2}/[0-9]{1,2})'; then
  touch_req "date_check"
fi

# MES 로그인/OAuth/실패 판정
if echo "$TEXT" | grep -qiE '(MES|로그인|OAuth|auth-dev|실패|수동 로그인|직접 로그인|세션 만료|redirect|리다이렉트)'; then
  touch_req "auth_diag"
fi

# 식별자/기준정보/SKILL 대조
if echo "$TEXT" | grep -qiE '(아이디가 다르|계정이 다르|식별자|기준정보|SKILL\.md|CLAUDE\.md|품번 불일치|identifier|account mismatch)'; then
  touch_req "skill_read"
  touch_req "identifier_ref"
fi

# 완료/갱신/반영/커밋
if echo "$TEXT" | grep -qiE '(완료|반영|갱신|커밋|푸시|HANDOFF|TASKS|STATUS|finish|종료)'; then
  touch_req "tasks_handoff"
fi

# 고위험 수정 (hard req): 자동화/운영 구조 변경만 차단 대상
# GPT 합의 2026-04-11: 규칙/리팩터/파이프라인 제거, 스키마/컬럼/시트는 lightweight 분리
if echo "$TEXT" | grep -qiE '(hook|gate|settings|마이그레이션|전수.*수정|일괄.*변경)'; then
  touch_req "map_scope"
fi

# 구조 변경 경고 (lightweight req): 차단 아닌 경고용. 스프레드시트/자동화 문맥에서만 참조
if echo "$TEXT" | grep -qiE '(스키마|컬럼|시트.*추가|시트.*삭제)'; then
  touch_req "map_scope_warn"
fi

# 스킬 사용 계측: /command 패턴 감지 시 skill_usage 로깅
SKILL_NAME=$(printf '%s' "$TEXT" | grep -oE '^\s*/([a-z][a-z0-9_-]*)' | sed 's|^\s*/||' | head -1)
if [ -n "$SKILL_NAME" ]; then
  hook_skill_usage "$SKILL_NAME" "slash"
fi

hook_log "UserPromptSubmit" "risk_profile_prompt reqs=${REQS:-none}"

# 출력은 선택사항. 최소 마찰 위해 추가 컨텍스트 미주입.
exit 0
