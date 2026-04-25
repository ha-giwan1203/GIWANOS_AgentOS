# Round 1 — GPT 본론

판정: **조건부 통과**

## A+B 조합: 적절
permissions.deny로 claude-in-chrome 호출 자체를 막고, navigate_gate.sh에 tool_name fallback을 두는 이중 방어는 과잉설계 아님. 다만 B는 URL 조건 전에 구 MCP tool_name이면 즉시 deny로 잡아야 함.

## PreToolUse 매처 6곳 처리: 그대로 두기 (단계적)
1차 커밋: deny + allow 제거 + fallback 추가
2차 커밋(검증 통과 후): 구 MCP 매처 제거
이유: deny 패턴 검증 전 매처까지 제거하면 실패 시 방어선 동시 소실.

## 추가 위험 1: 와일드카드 지원 검증 필수
permissions.deny 패턴이 와일드카드 `mcp__Claude_in_Chrome__*`를 실제로 지원하는지 smoke로 확인 필수. 지원 안 되면 "보기엔 막은 것 같은데 실제로는 뚫리는" 가짜 차단.

## 추가 위험 2: user-scope/local 설정 grep 검증
allow 7개 제거해도 다른 local/user scope 설정에 claude-in-chrome 허용 잔존 시 우회 가능. settings.json + settings.local.json + Claude user-scope MCP/permission 모두 grep 검증 필요.
