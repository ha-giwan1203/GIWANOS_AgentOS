#!/usr/bin/env bash
# [미사용 stub] /finish 자동 트리거 감지 hook — 폐기됨.
#
# 이력:
#   세션153           : 신설. UserPromptSubmit 이벤트에서 "끝/마무리" 발화 감지 시
#                       /finish 9단계 자동 진입 안내 메시지를 주입.
#   세션157 (2026-05-13): 안내 메시지 주입 비활성화 — 유도성 hook 제거(사용자 지시).
#                       쉘 골조만 남기고 exit 0 즉시 종료.
#   2026-05-22         : settings.json UserPromptSubmit 등록 해제. 현재 호출처 없음.
#
# 현재 정책: 종결 발화("끝"·"마무리"·"종료")는 Claude 자체 판단으로 처리한다.
#            hook 강제·자동 안내 없음. (CLAUDE.md "종결 발화 처리" 단락 참조)
# 이 파일은 이력 보존용 비활성 stub이다. settings 재등록 금지.
exit 0
