#!/bin/bash
# Stop hook — 금지 문구 차단 + 토론모드 필수 형식 검사
# Claude 응답 완료 직전에 실행. 위반 시 exit 2로 stop 차단.

TRANSCRIPT="$CLAUDE_TRANSCRIPT_PATH"

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  exit 0  # transcript 없으면 통과
fi

# 마지막 80줄만 검사 (전체 스캔 금지 — GPT 합의 2026-04-01)
TAIL=$(tail -n 80 "$TRANSCRIPT" 2>/dev/null)

# === 1. 금지 문구 검사 ===
FORBIDDEN_PATTERNS=(
  "전송할까요"
  "업데이트할까요"
  "진행할까요"
  "승인해주시면"
  "반영할까요"
  "이렇게 할까요"
  "확인해주시면"
)

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  if echo "$TAIL" | grep -q "$pattern"; then
    echo '{"decision":"block","reason":"[Stop Guard] 금지 문구 감지: '"$pattern"'. 사용자에게 중간 승인을 요청하지 마라. 합의 후 바로 실행하고 결과만 보고해라."}'
    exit 2
  fi
done

# === 2. 토론모드 필수 형식 검사 (채택/보류/버림) ===
# 토론모드 문맥 감지: "하네스 분석" 또는 "주장 분해" 또는 "debate" 키워드
if echo "$TAIL" | grep -qE "하네스 분석|주장 분해|채택.*버림|debate-mode|토론모드"; then
  HAS_ADOPT=$(echo "$TAIL" | grep -c "채택:")
  HAS_DISCARD=$(echo "$TAIL" | grep -cE "버림:|보류:")

  if [ "$HAS_ADOPT" -eq 0 ] && [ "$HAS_DISCARD" -eq 0 ]; then
    # 토론모드 문맥이지만 채택/버림 형식이 없으면 — 단순 전달일 수 있으므로 통과
    exit 0
  fi

  if [ "$HAS_DISCARD" -eq 0 ]; then
    echo '{"decision":"block","reason":"[Stop Guard] 토론모드에서 보류/버림이 0건. GPT 프레임을 그대로 수용한 것으로 판단. 주장 분해 → 라벨링 → 채택/보류/버림을 다시 수행하라."}'
    exit 2
  fi
fi

# 통과
exit 0
