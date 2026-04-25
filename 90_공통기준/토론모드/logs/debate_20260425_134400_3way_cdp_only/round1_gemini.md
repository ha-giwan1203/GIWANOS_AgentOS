# Round 1 — Gemini 본론 + GPT 검증

## 1단계 — GPT 응답 1줄 검증
verdict: **동의**
reason: 와일드카드 패턴 지원 여부 불확실성 + 로컬 환경(settings.local.json) 설정 누락 가능성 지적은 치명적 오류 예방의 매우 날카로운 지적.

## 2단계 — Gemini 독자 본론
판정: **조건부 통과**

### A+B 조합 적절성
적절함. Defense in Depth — 권한 레벨 원천 차단(A) + 스크립트 레벨 게이트웨이 폴백(B) 병행은 과잉설계 아닌 **필수 안전장치**.

### PreToolUse 매처 9곳 처리: **일괄 제거 권장** (GPT와 차이)
이미 대체 기술(CDP/chrome-devtools-mcp)이 실운영 검증을 마친 상태에서 사용하지 않는 레거시 매처를 단계적으로 남겨두는 것은 **예상치 못한 hook 찌꺼기 실행**을 유발할 수 있으므로 9곳 모두 단번에 정리.

### 추가 보완: 와일드카드 백업 플랜
permissions.deny에서 `mcp__Claude_in_Chrome__*` 와일드카드 미지원 시를 대비해 차단 대상 도구 이름을 **개별 문자열로 풀어서 하드코딩**하는 명시적 차단 백업 플랜 준비.

### 추가 위험 1건: settings.local.json BOM 충돌 재발 위험
`.claude/settings.local.json`은 Git 추적 제외 파일 + 개인화 설정. 스크립트 일괄 수정 시 세션107 BOM 충돌(Windows PowerShell 5 Set-Content -Encoding utf8) 재발 위험. **파일 갱신 전 반드시 백업 + 인코딩 방어 선행** 필수.
