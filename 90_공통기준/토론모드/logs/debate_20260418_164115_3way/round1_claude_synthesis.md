# Round 1 — Claude 종합 설계안 (의제2 토큰 임계치 경고 스킬)

## 스킬 정의
**이름**: `token-threshold-warn`
**역할**: 저장소 문서 비대화 **사전 감시기**. Claude Code 내장 `/cost`는 세션 누적 비용, 이 스킬은 **세션 시작 전 정적 문서 무게** 측정. 보완 관계, 중복 없음.

## 임계치 합의안 (양측 상향 수치)

| 대상 | 경고 | 강경고 | 측정 단위 |
|------|------|-------|----------|
| TASKS.md | 400줄 | 800줄 | 라인수 |
| HANDOFF.md | 500줄 | 800줄 | 라인수 |
| MEMORY.md 인덱스 | 120줄 | 200줄 | 라인수 |
| 개별 메모리 파일 총계 | 60개 | 100개 | 파일 개수 |
| incident_ledger.jsonl | 1MB | 3MB | 바이트 |

**근거**: GPT·Gemini 양측 동의. 현재 TASKS 약200줄·HANDOFF 약400줄 규모 대비 여유 확보 + 모델 지시 100% 인지 가독성 한계선 고려.

## 실행 지점

### SessionStart hook (`token_threshold_check.sh` 신규)
- 각 대상 빠르게 측정 (`wc -l`, `du -b`)
- 경고/강경고 초과 파일 목록 stderr 출력 (차단 안 함)
- 출력 형식: "파일: 현재치 / 임계치 / 감축 권고량 / 아카이브 후보"

### Stop hook (`token_threshold_delta.sh` 신규)
- 세션 종료 시 동일 측정 + 증가량 기록
- `incident_ledger.jsonl`에 `{"tag":"token_threshold", "file":"...", "delta":"+N줄"}` 추가
- 이후 세션 SessionStart에서 누적 증가 추세 참고

## 정책

### [MUST]
- 경고만. **차단 기능 도입 금지** — 제조업 자동화 환경 운영 리스크 (정산/배치 세션 차단 시 치명적)
- 측정 방식: 마크다운·텍스트 = 라인수, 로그·데이터 = 바이트
- SessionStart는 빠르게 유지 (토큰 근사치 측정 등 오버헤드 금지)

### [NEVER]
- 자동 아카이브 이동 — 시스템이 낡은 기록·현 맥락 임의 분리 시 사고 가능
- 토큰 근사치 계산 — 토크나이저 오버헤드, 결정성 부족

### [SHOULD]
- 강경고 시 수동 정리 스킬 권고 문구 출력 (예: `/memory-audit`, `98_아카이브/ 이동 후보`)
- 3회 연속 강경고 시 incident_ledger에 기록, 사용자 대시보드 알림

## 구현 단계
1. **Phase 1**: SessionStart hook만 (경고 출력)
2. **Phase 2** (1주 후): Stop hook 증가량 기록 추가
3. **Phase 3**: `/context` 공식 문서 확인 (context7 MCP) → 내장 컨텍스트 통계와 통합 리포트 (선택)

## 보류 항목
- `/context` 공식 내장 명령 존재 여부 — Claude Code 문서 확인 필요 (GPT 지적)
- 임계치 튜닝 — 1개월 운영 후 실제 경고 빈도 기반 재조정

## 근거
- GPT Round 1: `round1_gpt.md`
- Gemini Round 1: `round1_gemini.md`
- 교차 검증: `round1_cross_verify.md`
