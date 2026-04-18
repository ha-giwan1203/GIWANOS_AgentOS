# Round 1 — GPT 응답 (의제2 토큰 임계치)

## 요약
1. **내장 /cost와 중복 아님**. /cost는 세션 비용·지속시간·변경량 통계. 이 스킬은 저장소 문서 비대화 사전 점검 — 보완 관계. /context 내장 명령은 확실치 않음 → "/cost + context window + /compact"와 비교.
2. **임계치 상향**: 현재 초안 HANDOFF 300줄 경고는 도입 즉시 상시 경고. 추천 수치:
   - TASKS 350~400 / 700~800
   - HANDOFF 500 / 800
   - MEMORY 인덱스 120 / 200
   - 개별 메모리 60 / 100
   - incident_ledger.jsonl 1MB / 3MB
   - "자주 읽히는 문서" 위주로 잡기 (CLAUDE.md/auto memory/MCP/skill descriptions는 자동 적재)
3. **차단 임계 반대**. 경고만. SessionStart는 빠르게 유지 원칙.
4. **측정은 라인수 + 바이트**. 토큰 근사는 오버헤드.
5. **자동 아카이브 보류**. 수동 정리 명령만 후속.

## 권고 구조
- SessionStart: 빠른 측정 → 경고 출력만
- Stop: 같은 측정 + 증가량 기록
- 경고 레벨: 주의 / 강경고 2단계
- 출력: 어느 파일 초과·얼마 줄여야 정상·아카이브 후보
- 자동 조치 없음
