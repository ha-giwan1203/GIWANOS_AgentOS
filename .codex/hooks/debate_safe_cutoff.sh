#!/usr/bin/env bash
# debate_safe_cutoff.sh — 토론모드 가속 Safe-cutoff
# 4종 트리거 감지 시 .claude/state/debate_accel_disabled 생성 → 세션 가속 비활성
#
# 사용: gpt-send/gpt-read/gemini-send/gemini-read 내부에서 응답 수신 후 호출
#       또는 별도 advisory 등급 hook 등록
#
# 트리거 (1회라도 감지 시 즉시 비활성):
#   1. 인증 챌린지 화면 (Cloudflare challenge, captcha, 2FA 재요청)
#   2. 대화 기록 미저장 ("이 대화는 저장되지 않습니다" 등)
#   3. 사용량 경고·임시 제한 ("rate limit", "사용량 초과", "한도")
#   4. 보안 알림 ("계정 보호", "비정상 활동")
#
# 입력: stdin에 응답 텍스트 또는 페이지 HTML 일부
# 출력: 트리거 시 exit 0 + .claude/state/debate_accel_disabled 생성
#       감지 없음 시 exit 0 무동작
#
# 세션157 3way R1 합의 (pass_ratio=1.00) — Gemini Safe-cutoff 제안 반영

set -u

STATE_DIR=".claude/state"
DISABLE_FILE="${STATE_DIR}/debate_accel_disabled"
LOG_FILE=".claude/hooks/safe_cutoff.log"

mkdir -p "${STATE_DIR}"

# 이미 비활성화된 경우 즉시 종료
if [[ -f "${DISABLE_FILE}" ]]; then
  exit 0
fi

# stdin에서 검사 대상 텍스트 읽기
INPUT=$(cat 2>/dev/null || echo "")

if [[ -z "${INPUT}" ]]; then
  exit 0
fi

TRIGGER=""

# 1. 인증 챌린지 (Cloudflare / captcha / 2FA)
if echo "${INPUT}" | grep -qiE "cloudflare|captcha|verify you are human|verification required|2단계 인증|보안 인증|이상한 활동"; then
  TRIGGER="auth_challenge"
fi

# 2. 대화 기록 미저장
if [[ -z "${TRIGGER}" ]] && echo "${INPUT}" | grep -qiE "대화는 저장되지|not saved|chat (will )?not.*saved|temporary chat|일시적인 대화"; then
  TRIGGER="conversation_not_saved"
fi

# 3. 사용량 경고·임시 제한
if [[ -z "${TRIGGER}" ]] && echo "${INPUT}" | grep -qiE "rate limit|usage limit|사용량.*초과|한도.*초과|too many requests|quota exceeded|일시적으로.*제한"; then
  TRIGGER="rate_limit"
fi

# 4. 보안 알림
if [[ -z "${TRIGGER}" ]] && echo "${INPUT}" | grep -qiE "계정.*보호|account.*protection|비정상.*활동|suspicious activity|보안.*경고"; then
  TRIGGER="security_alert"
fi

# 트리거 감지 → 가속 비활성화
if [[ -n "${TRIGGER}" ]]; then
  TS=$(date "+%Y-%m-%d %H:%M:%S")
  echo "${TS}|trigger=${TRIGGER}" > "${DISABLE_FILE}"
  echo "[${TS}] DEBATE_ACCEL_DISABLED trigger=${TRIGGER}" >> "${LOG_FILE}"

  # 사용자 알림 (stderr) — advisory 등급으로 차단 안 함
  echo "[debate_safe_cutoff] 가속 모드 비활성화: ${TRIGGER}. UI fallback 자동 전환. 해제: rm ${DISABLE_FILE}" >&2
fi

exit 0
