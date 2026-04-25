# Round 1 — Claude 독자안 (선행 작성)

세션: 107 (2026-04-25 KST)
의제: 토론모드 CDP 단독 사용 정책 — 실행 차단 강제 (B 분류 자동 승격)
배경: 사용자 옵션 2 선택. 정책 명시(커밋 177d5160) 후 실제 차단 강제 단계.

## 독립 분석 (실물 근거)

### 1. 현재 상태 (실측)
- `.claude/settings.json` permissions.allow에 claude-in-chrome MCP 7개 등록:
  - line 53: `mcp__Claude_in_Chrome__tabs_context_mcp`
  - line 54: `mcp__Claude_in_Chrome__navigate`
  - line 55: `mcp__Claude_in_Chrome__javascript_tool`
  - line 56: `mcp__Claude_in_Chrome__get_page_text`
  - line 57: `mcp__Claude_in_Chrome__computer`
  - line 76: `mcp__Claude_in_Chrome__tabs_create_mcp`
  - (form_input은 별도)
- PreToolUse 매처 6곳 (line 190, 235, 244, 262, 327, 336)에 claude-in-chrome 매처 잔존
- `permissions.deny` 블록 부재 → 명시 차단 정책 없음

### 2. 차단 옵션 비교

| 옵션 | 방식 | 강도 | 부작용 |
|------|------|------|-------|
| A | `permissions.deny`에 `mcp__Claude_in_Chrome__*` 패턴 추가 | 강 (MCP 호출 자체 거부) | 토론모드 외 사용도 차단 |
| B | navigate_gate.sh에 tool_name 검사 추가 | 중 (hook deny) | gate가 fail-open 시 우회 가능 |
| C | settings.json PreToolUse 매처 6곳 제거 | 약 (gate 미발동) | **역효과 — 오히려 차단 약화** |
| D | `permissions.allow`에서 claude-in-chrome 7개 제거 | 약 (allow 제거) | Claude Code가 미정의 권한으로 ask 모드로 전환 가능 |

### 3. Claude 독자안: A + B 조합

**A — settings.json `permissions.deny` 추가 (주 차단)**:
```json
"deny": [
  "mcp__Claude_in_Chrome__*"
]
```
- MCP 호출 자체 거부. 가장 강력
- 토론모드 외에서도 차단. 단 chrome-devtools-mcp가 동일 기능(navigate_page, evaluate_script, click, fill, take_snapshot 등) 모두 제공 → 영향 없음
- 우회 불가능 (Claude Code 정책 레이어 enforcement)

**B — navigate_gate.sh fallback (보조 차단)**:
```bash
# 추가 로직 (chatgpt.com URL 체크 전)
if echo "$TOOL_NAME" | grep -q '^mcp__Claude_in_Chrome__'; then
  echo "{...permissionDecision:deny...토론모드는 chrome-devtools-mcp 단독 사용...}"
  hook_incident "gate_reject" "navigate_gate" "" "claude-in-chrome 호출 차단" '"classification_reason":"cdp_only_policy"'
  exit 0
fi
```
- A가 정책 레이어에서 차단 못 한 경우 (matcher 누락 등) hook gate 추가 방어선
- belt-and-suspenders 패턴

### 4. 회귀 위험 분석
**낮음 ~ 중**:
- chrome-devtools-mcp가 모든 기능 대체 가능 → 운영 영향 없음
- 위험 1: claude-in-chrome MCP가 토론모드 외에서 일회성으로 사용된 적 있을 수 있음 (스크린샷·페이지 텍스트 등). grep 결과 settings/hook/스킬에만 등장 → 실 사용 거의 없음
- 위험 2: settings.json deny 신설 시 형식 오류 → JSON 파싱 깨짐. 사전 검증 필수 (python json.load)
- 위험 3: navigate_gate.sh fallback 추가 시 토론모드 외 chrome-devtools-mcp navigate가 chatgpt.com URL이면 동일 차단 (현 동작). 신규 차단은 tool_name 검사뿐 → 영향 격리

### 5. 부수 효과
**긍정**:
- 정책-실행 일치 (세션107 사용자 지시 정책 명시 + 실 차단 강제)
- L-4 [3way] 합의안 (navigate_gate 보호자산 등록)과 일관 — 외부 연동 진입점 보안 강화
- chrome-devtools-mcp 단일 경로 → 운영 단순화

**부정**:
- claude-in-chrome MCP 사용자 화면 대화에서 "스크린샷 보여줘" 같은 일반 요청 차단됨 → chrome-devtools-mcp의 take_screenshot으로 대체 안내 필요
- settings.json line 53-57, 76 entries는 deny와 충돌하므로 정리 권고

### 6. 적용 단계 (3단계)
1. **settings.json deny 추가**: permissions 블록에 `"deny": ["mcp__Claude_in_Chrome__*"]` 신설
2. **settings.json allow 정리**: line 53-57, 76의 claude-in-chrome 6개 entries 제거 (deny와 충돌 방지)
3. **navigate_gate.sh fallback 추가**: tool_name 검사 deny 분기 (line 27 TOOL_NAME 추출 후)

### 7. PreToolUse 매처 6곳 처리
- 매처 자체는 그대로 두기 (matcher가 deny된 도구를 잡을 일 없으므로 비활성)
- 또는 cleanup으로 함께 제거 (별 의제 — settings.json 구조 단순화)

## 결론
**A + B 조합 적용**.
- A (deny + allow 정리): 주 차단
- B (navigate_gate fallback): 보조 방어
- 회귀 위험 낮음~중. chrome-devtools-mcp 대체 가능. 사전 JSON 검증 필수
- L-4 합의안과 정합 (외부 연동 진입점 보안 강화)

## 검증 요청 (양측)
1. **A+B 조합 적절성**: deny + hook fallback 이중 방어가 적정 수준인지? 과잉 설계인가?
2. **PreToolUse 매처 6곳 처리**: 그대로 둘지(비활성), 함께 제거할지(구조 단순화)?
3. **추가 위험 또는 보완 필요 항목**: 분석에서 놓친 부분이 있는지?
