# Q4 Round 1 — Gemini (Claude-Gemini 토론파트너 Gem)

## Step 6-2 GPT 검증 (1줄)
verdict: 동의
reason: URL을 신규 로드하는 도구(navigate_page, new_page)만 통제 대상에 추가하고 단순 탭 전환 도구(select_page)를 제외하는 것은, 보안 원칙을 유지하면서도 오탐을 최소화하는 가장 정확하고 실용적인 접근입니다.

## Step 6-3 본론

### 결론
Q4 = **A안 채택** (최소보강 — navigate_page/new_page 매처 확장 및 select_page 제외)

### 핵심 주장

1. **[실증됨] 신규 진입 경로 보안 구멍**
   - 세션105 MCP 전환으로 발생한 신규 진입 경로(new_page, navigate_page)는 기존 navigate_gate.sh의 단일 매처 구조에서 누락
   - 이를 포함시키는 것은 보안 구멍을 메우는 필수 조치

2. **[일반론] 오탐 축소 근거**
   - 11건 incident 중 단순 탭 전환 동작이 차단된 오탐(False Positive) 일부(0~3건) 가능성
   - 새로운 URL 로딩이 없는 select_page 제외는 탐지 정확도 향상의 합리적 결정

3. **[과잉설계] B안 비판**
   - B안(skill-only 강제)은 훅 목적을 넘어선 권한 통제
   - 정상 브라우저 조작 스킬의 유연성을 저해 → 향후 운영 효율 감소

### 반대 안 약점

- **B안**: 문지기를 고치는 대신 길 자체를 봉쇄하는 격 → 향후 스킬 확장에 장애물, 과잉설계
- **C안**: 신규 MCP 우회 경로가 열린 상태에서 기본 방어선마저 철거 → 보안 커버리지의 심각한 후퇴

### 착수·완료·검증 조건

- 착수: settings.json PreToolUse 단계에 navigate_page + new_page 매처 추가
- 완료 기준: navigate_gate.sh 스크립트에 new_page(tool_input.url)와 navigate_page(tool_input.url, type="url") 파싱 로직 구현 + select_page 제외 처리
- 검증 방법: 실운영 테스트 — select_page 실행 시 게이트 우회 확인, new_page/navigate_page 실행 시 정상 게이트 통제(차단/승인) 작동
- 재라운드 트리거: 반영 후 7일 이내 정상 스킬 실행이 게이트에 의해 부당 차단되는 오탐 사례 3건 이상 발생 시 재상정
