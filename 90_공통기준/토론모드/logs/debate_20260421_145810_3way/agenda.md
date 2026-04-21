# Agenda — B4: Self-Limiting (Layer 4 안전장치)

**의제**: self-X 자체가 폭주하지 않도록 통제. circuit breaker + 메타루프 방지 + 자동 변경 상한
**모드**: 3자 토론, 상호 감시 프로토콜
**B 분류 근거**: 자가 수정 시스템의 안전 정책 신설 — 실행 흐름·차단 정책 변경

## 배경

플랜 `wobbly-prancing-forest.md` Layer 4 영역. B2/B3 (Self-Recovery / Self-Evolution) 도입 전 선행 필수.
배경 위험:
- B2 도입 후 Claude가 자동으로 hook/skill/state 수정 → 잘못된 수정 누적 위험
- B3 자동 승급 ("5회 성공 → T1 승격") 잘못된 패턴 자동화 위험
- 메타루프: self-X가 self-X를 수정하는 무한 변경 가능성

## Claude 독립 의견

### D1. 자동 변경 일일 상한
- ① 보수: T1 일일 5건
- ② 중도: T1 일일 10건 + T2 일일 3건
- ③ 공격: 상한 없음 (circuit breaker만)
**Claude**: ②중도. T1=자동 cleanup·rotation 등 저위험. T2=hook 임계값 변경 등 중위험. 상한 차이 둠.

### D2. Circuit Breaker 트리거
- ① 24h 동일 영역 N회 변경 (예: N=5)
- ② 24h smoke_test 실패율 > 임계
- ③ 사용자 명시적 일시정지
**Claude**: ①+②+③ 병행. 동일 영역 5회 + smoke 실패 1회라도 + override.

### D3. 잠금 해제 방식
- ① 24h 자동 해제
- ② 사용자 명시 승인만
- ③ 원인 해소 후 자동 해제 (smoke PASS + 24h 무사고)
**Claude**: ②+③ 결합. 자동 해제는 ③조건 충족 시 + 결정적 원인 해소 입증, 외엔 사용자 승인.

### D4. 메타 invariant
- ① self-X 자체 health 추적 (변경 빈도·실패율)
- ② Layer 1 invariant에 통합
- ③ 별도 self-meta 영역 (Layer 4 전용)
**Claude**: ③별도. B5에서 invariant Layer 분리 합의했음. self-X 메타도 동일 원칙.

### D5. 잘못된 변경 롤백 메커니즘
- ① 모든 self-X 변경 = git commit 단위 (revert로 복구)
- ② 별도 transaction log + rollback 명령
- ③ 사용자 수동만
**Claude**: ①. git이 이미 transaction 시스템. 추가 인프라 불필요.

## 추가 위험 식별
- circuit breaker 자체가 과민 작동 시 정상 운영 마비
- 메타 invariant가 메타 메타 invariant 필요 → 무한 회귀 위험
- "원인 해소 입증" 자동 판정의 객관성 확보 어려움

## 5가지 질문
1. D1~D5 동의/이의/추가 안?
2. T1/T2 일일 상한 적정 수치?
3. Circuit breaker 과민 작동 방지책?
4. 메타 invariant 무한 회귀 차단 깊이?
5. "원인 해소 입증" 자동 판정 객관 기준?

응답 형식: 각 1~3문장. 한국어. B 분류 깊은 비판 환영.
