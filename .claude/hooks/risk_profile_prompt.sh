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
# GPT 합의 2026-04-12: 단순 언급이 아니라 변경 의도 키워드와 AND 조건
# 이전: hook|gate|settings 단독 → 일상 대화에서도 40건+ 반복 차단 발생
HAS_TARGET=$(echo "$TEXT" | grep -ciE '(hook|gate|settings|마이그레이션)')
HAS_INTENT=$(echo "$TEXT" | grep -ciE '(수정|변경|삭제|리팩터|제거|추가|교체|이동|전수|일괄)')
if [ "$HAS_TARGET" -gt 0 ] && [ "$HAS_INTENT" -gt 0 ]; then
  touch_req "map_scope"
fi

# 구조 변경 경고 (lightweight req): 차단 아닌 경고용. 스프레드시트/자동화 문맥에서만 참조
if echo "$TEXT" | grep -qiE '(스키마|컬럼|시트.*추가|시트.*삭제)'; then
  touch_req "map_scope_warn"
fi

# 토론 도메인 감지 → debate_preflight.req 생성
# GPT 합의(세션25): 토론 키워드 감지 시 harness_gate 활성화용 req 생성
if echo "$TEXT" | grep -qiE '(토론|GPT.*공유|GPT.*판정|하네스|harness|debate|채택.*보류|반박문|share.result)'; then
  touch_req "debate_preflight"
fi

# 도메인 진입 감지 → active_domain.req 생성
# GPT 합의(세션33): UserPromptSubmit에서 키워드 매칭 → 활성 도메인 기록
DOMAIN_REGISTRY="$PROJECT_ROOT/.claude/domain_entry_registry.json"
DOMAIN_REQ="$PROJECT_ROOT/.claude/state/active_domain.req"
if [ -f "$DOMAIN_REGISTRY" ]; then
  MATCHED_DOMAIN=""
  MATCHED_KEYWORD=""
  MATCHED_PRIORITY=999
  # priority 순으로 JSON 파싱 (jq 없이 grep+sed)
  DOMAIN_COUNT=$(grep -c '"domain_id"' "$DOMAIN_REGISTRY" 2>/dev/null || echo 0)
  for i in $(seq 0 $((DOMAIN_COUNT - 1))); do
    # 각 도메인 블록에서 keywords 추출
    BLOCK=$(awk -v idx="$i" 'BEGIN{c=-1} /\{/{c++} c==idx{print} /\}/{if(c==idx) c=999}' "$DOMAIN_REGISTRY")
    D_ID=$(echo "$BLOCK" | grep '"domain_id"' | sed 's/.*: *"//;s/".*//')
    D_PRI=$(echo "$BLOCK" | grep '"priority"' | sed 's/.*: *//;s/,.*//')
    D_KEYWORDS=$(echo "$BLOCK" | grep -oE '"keywords"[^]]*\]' | grep -oE '"[^"]*"' | tail -n +2 | sed 's/"//g')
    for kw in $D_KEYWORDS; do
      if echo "$TEXT" | grep -qiF "$kw"; then
        if [ "${D_PRI:-999}" -lt "$MATCHED_PRIORITY" ]; then
          MATCHED_DOMAIN="$D_ID"
          MATCHED_KEYWORD="$kw"
          MATCHED_PRIORITY="$D_PRI"
        fi
        break
      fi
    done
  done
  if [ -n "$MATCHED_DOMAIN" ]; then
    # required_doc_ids 추출
    BLOCK=$(awk -v did="$MATCHED_DOMAIN" '$0 ~ "\"domain_id\".*\""did"\""{found=1} found{print} found && /\]/{if(p) exit} found && /required_docs/{p=1}' "$DOMAIN_REGISTRY")
    DOC_IDS=$(echo "$BLOCK" | grep '"id"' | sed 's/.*: *"//;s/".*//' | tr '\n' ',' | sed 's/,$//')
    mkdir -p "$(dirname "$DOMAIN_REQ")"
    printf 'domain_id=%s\nmatched_keyword=%s\nrequired_doc_ids=%s\n' "$MATCHED_DOMAIN" "$MATCHED_KEYWORD" "$DOC_IDS" > "$DOMAIN_REQ"
    hook_log "UserPromptSubmit" "active_domain=$MATCHED_DOMAIN keyword=$MATCHED_KEYWORD"
  else
    rm -f "$DOMAIN_REQ" 2>/dev/null || true
  fi
fi

# 스킬 사용 계측: /command 패턴 감지 시 skill_usage 로깅
# 주의: TEXT는 JSON 래핑 포함. ^ 앵커 사용 불가 (2026-04-12 세션24 수정)
SKILL_NAME=$(printf '%s' "$TEXT" | grep -oE '"/([a-z][a-z0-9_-]*)' | sed 's|^"/||' | head -1)
if [ -n "$SKILL_NAME" ]; then
  hook_skill_usage "$SKILL_NAME" "slash"
fi

hook_log "UserPromptSubmit" "risk_profile_prompt reqs=${REQS:-none}"

# 출력은 선택사항. 최소 마찰 위해 추가 컨텍스트 미주입.
exit 0
