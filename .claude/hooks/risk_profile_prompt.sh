#!/bin/bash
# UserPromptSubmit — 현재 사용자 프롬프트 기준 req 생성
# 주의: 요청마다 req를 재생성한다. 이전 req 누적 금지.
#
# req clear 규칙 3조건 (세션49 GPT 합의, 세션52 실물검증→문서화 종결):
#   조건1(위험 미검출): line 23 find -delete로 매 프롬프트 기존 req 전삭제 → 키워드 미매칭 시 req 미생성
#   조건2(ok 존재 시 억제): touch_req()에서 fresh .ok 파일 존재 시 req 재발행 억제 (bb52c08 반복 차단)
#   조건3(작업단계 전환): 매 프롬프트 재생성 구조로 흡수 — 단계 전환 시 새 프롬프트가 기존 req를 자동 교체

source "$(dirname "$0")/hook_common.sh" 2>/dev/null
# 훅 등급: measurement (Phase 2-C 2026-04-19 세션73 timing 배선)
_RPP_START=$(hook_timing_start)

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
  # GPT 합의 세션49 req clear 규칙 2: 대응 ok 존재 시 req 재발행 억제
  # 동일 핑거프린트 반복 차단(bb52c08) 근본 해결
  if [ -f "$PROOF_DIR/$name.ok" ] && [ "$PROOF_DIR/$name.ok" -nt "$START_FILE" ]; then
    hook_log "UserPromptSubmit" "req_suppress=$name (fresh ok exists)"
    return 0
  fi
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

# 식별자/기준정보 대조 (evidence-core: identifier_ref)
# 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 4번 (c)):
#   skill_read req 제거 → skill_instruction_gate가 SKILL.md 읽기 전담
#   identifier_ref는 evidence-core로 유지
# 세션78 P2 재정의: "식별자", "기준정보" 제거 (일상 대화 빈도 높음 → 과탐지)
if echo "$TEXT" | grep -qiE '(아이디가 다르|계정이 다르|품번 불일치|identifier|account mismatch)'; then
  touch_req "identifier_ref"
fi

# 세션93 (2026-04-22 2자 토론 합의, plan.md 1주차 4번 (b)):
#   map_scope / map_scope_warn req 발행 제거. evidence 버스에서 분리.
#   이유: evidence-core 3종(date_check/auth_diag/identifier_ref)에 집중하기 위함.
#   /map-scope 스킬은 Claude 자발적 선언 경로로 유지 (강제 req 없이 원칙 실천).
# 세션78 P2 재정의: tasks_handoff 조기 트리거 완전 제거 (위 히스토리 유지)
# 세션77 Round 1 Step 1-c: HAS_HOOK_FILE/HAS_SETTINGS/HAS_MIGRATION AND HAS_INTENT 로직이 있었으나 세션93에서 블록 제거

# 토론 도메인 감지 → debate_preflight.req 생성
# GPT 합의(세션25): 토론 키워드 감지 시 harness_gate 활성화용 req 생성
# 세션47 확장: 토론/공동/공유 모두 동일 조건 — 우회 접근 차단
if echo "$TEXT" | grep -qiE '(토론|공동작업|공동|GPT.*공유|GPT.*판정|하네스|harness|debate|채택.*보류|반박문|share.result|토론방)'; then
  touch_req "debate_preflight"
fi

# 도메인 진입 감지 → active_domain.req 생성
# GPT 합의(세션33): UserPromptSubmit에서 키워드 매칭 → 활성 도메인 기록
DOMAIN_REGISTRY="$PROJECT_ROOT/.claude/domain_entry_registry.json"
DOMAIN_REQ="$PROJECT_ROOT/.claude/state/active_domain.req"
if [ -f "$DOMAIN_REGISTRY" ]; then
  # GPT FAIL 대응: awk 블록 카운터 오류 + 공백 키워드 분리 수정
  # 접근: 임시 파일에 매칭 후보를 기록, priority 정렬로 최우선 선택
  MATCH_TMP=$(mktemp)
  CUR_ID="" CUR_PRI="" IN_KW=0
  while IFS= read -r line; do
    if echo "$line" | grep -q '"domain_id"'; then
      CUR_ID=$(echo "$line" | sed 's/.*: *"//;s/".*//')
      CUR_PRI="" IN_KW=0
    fi
    if echo "$line" | grep -q '"priority"'; then
      CUR_PRI=$(echo "$line" | sed 's/.*: *//;s/[^0-9]//g')
    fi
    if echo "$line" | grep -q '"keywords"'; then
      IN_KW=1
    fi
    if [ "$IN_KW" -eq 1 ]; then
      # 공백 포함 키워드를 원자 단위로 추출
      while IFS= read -r kw; do
        [ -z "$kw" ] && continue
        if echo "$TEXT" | grep -qiF "$kw"; then
          printf '%s\t%s\t%s\n' "${CUR_PRI:-999}" "$CUR_ID" "$kw" >> "$MATCH_TMP"
        fi
      done <<< "$(echo "$line" | grep -oE '"[^"]*"' | grep -v 'keywords' | sed 's/"//g')"
      if echo "$line" | grep -q '\]'; then
        IN_KW=0
      fi
    fi
  done < "$DOMAIN_REGISTRY"

  # priority 최소값 선택 (첫 일치 승리)
  BEST=$(sort -t$'\t' -k1 -n "$MATCH_TMP" | head -1)
  rm -f "$MATCH_TMP"

  if [ -n "$BEST" ]; then
    MATCHED_PRIORITY=$(echo "$BEST" | cut -f1)
    MATCHED_DOMAIN=$(echo "$BEST" | cut -f2)
    MATCHED_KEYWORD=$(echo "$BEST" | cut -f3)
    # required_doc_ids 추출
    DOC_IDS=""
    IN_TARGET=0 IN_DOCS=0
    while IFS= read -r dline; do
      if echo "$dline" | grep -q "\"$MATCHED_DOMAIN\""; then
        IN_TARGET=1
      fi
      if [ "$IN_TARGET" -eq 1 ] && echo "$dline" | grep -q '"required_docs"'; then
        IN_DOCS=1
      fi
      if [ "$IN_TARGET" -eq 1 ] && [ "$IN_DOCS" -eq 1 ]; then
        DID=$(echo "$dline" | grep '"id"' | sed 's/.*: *"//;s/".*//')
        if [ -n "$DID" ]; then
          DOC_IDS="${DOC_IDS}${DOC_IDS:+,}$DID"
        fi
        if echo "$dline" | grep -q '^\s*\]'; then
          IN_DOCS=0 IN_TARGET=0
        fi
      fi
    done < "$DOMAIN_REGISTRY"
    mkdir -p "$PROJECT_ROOT/.claude/state"
    printf 'domain_id=%s\nmatched_keyword=%s\nrequired_doc_ids=%s\n' \
      "$MATCHED_DOMAIN" "$MATCHED_KEYWORD" "$DOC_IDS" > "$DOMAIN_REQ"
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

# 토론 도메인 감지 시 debate-mode 스킬 사용 안내 주입 (세션47)
# 수동 브라우저 조작·gpt-send 우회 방지
if [ -f "$REQ_DIR/debate_preflight.req" ]; then
  echo '{"systemMessage":"[토론 절차 안내] 토론/공동작업 관련 요청입니다. 반드시 debate-mode 스킬을 사용하세요.\n- Skill 도구로 debate-mode 호출\n- 수동 navigate/gpt-send 사용 금지\n- debate-mode가 지침 읽기 → 탭 준비 → 전송 절차를 자동 처리합니다."}'
  hook_timing_end "risk_profile_prompt" "$_RPP_START" "debate_inject"
  exit 0
fi

hook_timing_end "risk_profile_prompt" "$_RPP_START" "ok"
exit 0
