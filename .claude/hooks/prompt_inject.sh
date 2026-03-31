#!/bin/bash
# UserPromptSubmit hook — 토론모드/공동작업 시 체크리스트 자동 주입
# 사용자 프롬프트에 토론/공동작업 키워드가 있으면 하네스 체크리스트를 컨텍스트로 주입

# stdin에서 hook 입력 읽기
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    obj = json.loads(sys.stdin.read())
    print(obj.get('prompt', ''))
except:
    pass
" 2>/dev/null)

# 토론모드/공동작업 키워드 감지
if echo "$PROMPT" | grep -qiE "토론모드|debate-mode|gpt.*토론|gpt.*물어|gpt.*알려|공동작업|GPT.*의견"; then
  echo '{"additionalContext":"[Hook 자동 주입] 토론모드/공동작업 하네스 체크리스트:\n1. GPT 응답 수신 후 반드시 주장 분해 → 라벨링(실증/일반론/환경미스매치/과잉) → 채택/보류/버림 판정 수행\n2. 반박문 첫 문단에 채택:/보류:/버림: 필수 포함. 버림 0건이면 재분해\n3. 사용자에게 중간 승인 요청 금지. 합의 후 즉시 실행 → GPT 공유 → 추가수정 루프\n4. 허용 문장: \"이 기준으로 바로 적용한다\", \"합의 반영 후 결과만 보고한다\"\n5. 입력 전 미확인 응답 점검 필수 (Step 1.5)"}'
fi

exit 0
