#!/bin/bash
# PreCompact: 컨텍스트 압축 전 핵심 규칙 자동 재주입
# 컴팩션 시 유실되면 안 되는 운영 규칙을 강제 주입
# 합의: GPT+Claude 2026-04-01

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# 현재 브랜치
BRANCH=$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo "unknown")

# 변경 파일 목록 (최근 세션)
DIRTY_FILES=""
if [ -f "$PROJECT_DIR/.claude/dirty.flag" ]; then
  DIRTY_FILES=$(cat "$PROJECT_DIR/.claude/dirty.flag" 2>/dev/null | head -20)
fi

cat <<INJECT
{"message":"[PreCompact 핵심 규칙 재주입]
■ 상태 원본: TASKS.md (1순위) > STATUS.md > HANDOFF.md
■ 원본 파일 직접 수정 금지 (명시 요청 시에만)
■ 검증 없이 완료 처리 금지
■ 공동작업: GPT 제안은 검증 후 반영, 맹목 수용 금지
■ Plan-First: plan.md 승인 전 구현 금지
■ 현재 브랜치: $BRANCH
■ 미검증 변경 파일: ${DIRTY_FILES:-없음}
■ 컴팩션 후에도 위 규칙 유지 필수"}
INJECT
exit 0
