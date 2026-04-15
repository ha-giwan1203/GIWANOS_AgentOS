#!/bin/bash
# PreToolUse(Bash) — 스킬 지침 강제읽기 + MES/ZDM 작업순서 검증
#
# 1. 인라인 python(ad-hoc) 스크립트에서 MES/ZDM 접근 시 → 해당 SKILL.md 읽기 강제
# 2. MES SaveExcelData.do 호출 시 → selectPrdtRsltByLine.do(기등록 확인) 포함 강제
#
# 정식 스킬 run.py 실행은 통과 (스케줄 태스크 호환 + 스크립트 내부에 순서 내장)
# 인라인 스크립트만 게이트 — 진단/수동 작업 시 지침 무시 방지

source "$(dirname "$0")/hook_common.sh" 2>/dev/null

INPUT="$(cat)"
COMMAND="$(echo "$INPUT" | safe_json_get "command" 2>/dev/null)"

# 정식 스킬 run.py 실행은 통과 (내부에 작업순서 내장)
if echo "$COMMAND" | grep -qE '스킬/[^/]+/run\.py'; then
  exit 0
fi

# 인라인 python 감지 (python3 - <<, python3 -c, PYTHONIOENCODING=utf-8 python3 -)
# 명령이 (환경변수=값)* python3 - 로 시작하는 경우만 — heredoc/파일 내부 문자열 오탐 방지
is_inline_python() {
  echo "$COMMAND" | grep -qE "^([A-Za-z_]+=[^ ]+ )*python3?\s+(-\s|(-c\s))"
}

if ! is_inline_python; then
  exit 0
fi

evidence_init

# ── MES 시스템 접근 검사 ──
if echo "$COMMAND" | grep -qF 'mes-dev.samsong.com'; then
  # SKILL.md 읽기 확인
  if ! fresh_ok "skill_read__daily-routine" && ! fresh_ok "skill_read__production-result-upload"; then
    MSG="[skill_instruction_gate] MES 접근 차단: SKILL.md 미읽기.\\n먼저 daily-routine 또는 production-result-upload SKILL.md를 읽으세요.\\n  Read(90_공통기준/스킬/daily-routine/SKILL.md)\\n  Read(90_공통기준/스킬/production-result-upload/SKILL.md)"
    hook_log "skill_instruction_gate" "DENY mes_access_no_skillmd"
    hook_incident "gate_reject" "skill_instruction_gate" "" "MES access without SKILL.md read" \
      "\"classification_reason\":\"evidence_missing\""
    echo "{\"decision\":\"deny\",\"reason\":\"$MSG\"}"
    exit 0
  fi

  # MES 업로드 작업순서: SaveExcelData.do 호출 시 기등록 확인 포함 강제
  if echo "$COMMAND" | grep -qF 'SaveExcelData.do'; then
    if ! echo "$COMMAND" | grep -qF 'selectPrdtRsltByLine.do'; then
      MSG="[skill_instruction_gate] MES 업로드 차단: 기등록 확인 누락.\\nSKILL.md 작업순서: 기등록 조회(selectPrdtRsltByLine.do) -> 업로드 -> 검증.\\n스크립트에 기등록 확인 단계를 포함하세요."
      hook_log "skill_instruction_gate" "DENY mes_upload_no_precheck"
      hook_incident "gate_reject" "skill_instruction_gate" "" "MES upload without pre-check (selectPrdtRsltByLine.do missing)" \
        "\"classification_reason\":\"evidence_missing\""
      echo "{\"decision\":\"deny\",\"reason\":\"$MSG\"}"
      exit 0
    fi
  fi
fi

# ── ZDM 시스템 접근 검사 ──
if echo "$COMMAND" | grep -qF 'ax.samsong.com'; then
  if ! fresh_ok "skill_read__daily-routine" && ! fresh_ok "skill_read__zdm-daily-inspection"; then
    MSG="[skill_instruction_gate] ZDM 접근 차단: SKILL.md 미읽기.\\n먼저 daily-routine 또는 zdm-daily-inspection SKILL.md를 읽으세요."
    hook_log "skill_instruction_gate" "DENY zdm_access_no_skillmd"
    hook_incident "gate_reject" "skill_instruction_gate" "" "ZDM access without SKILL.md read" \
      "\"classification_reason\":\"evidence_missing\""
    echo "{\"decision\":\"deny\",\"reason\":\"$MSG\"}"
    exit 0
  fi
fi

hook_log "skill_instruction_gate" "PASS"
exit 0
