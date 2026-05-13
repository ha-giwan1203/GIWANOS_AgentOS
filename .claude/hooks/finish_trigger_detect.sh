#!/usr/bin/env bash
# /finish 자동 트리거 감지 — 사용자 발화에서 작업 종결 키워드 검출 시 Claude에 advisory 알림
# 세션153 신설. 단순 인사로 받지 않게 명시적 system-reminder 주입.
# Exit 0 강제 (advisory — 차단 X). stdout JSON으로 Claude에 추가 컨텍스트 전달.

set -eu

input="$(cat)"

# user_prompt 추출 — python 우선, 실패 시 grep fallback
prompt=$(python -c "import sys, json; d=json.load(sys.stdin); print(d.get('user_prompt') or d.get('prompt') or '')" <<<"$input" 2>/dev/null || \
         echo "$input" | grep -oE '"(prompt|user_prompt)":"[^"]*"' | head -1 | sed 's/.*":"//;s/"$//' || echo "")

# 트리거 키워드 (작업 종결 의지 명확 발화)
# - 단순 "수고했다" 단독은 인사 가능성 있어 제외
# - "마무리"·"끝"·"종료" + 동사형 결합 필수
if echo "$prompt" | grep -qE '(마무리하자|마무리 하자|마무리 짓자|마무리 짓고|이제 마무리|이걸로 마무리|끝내자|오늘 끝|작업 끝|작업끝|이걸로 끝|종료하자|종료 하자|수고했다.*마무리|수고했다.*끝)'; then
    cat << 'EOF'
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "[/finish 자동 트리거 감지] 사용자 발화에 작업 종결 의지 키워드 포함. CLAUDE.md 핵심 원칙 + feedback_finish_auto_trigger.md에 따라 즉시 /finish 9단계 자동 진입. 단순 인사로 해석 금지 — Skill 도구로 finish 호출 권고."}}
EOF
fi
exit 0
