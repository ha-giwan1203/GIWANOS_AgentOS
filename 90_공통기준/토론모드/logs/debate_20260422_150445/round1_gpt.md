# Round 1 — GPT 응답 (개선 계획 초안)

## 핵심 결론
전면 재설계 대신 **evidence 축을 먼저 강하게 축소**한 뒤 남는 핵심 계약만 재설계. 이게 전체 시스템을 더 단순하게 만듦.

## 1단 — 구조 단위 분류

### evidence 축
- 공통 원인: 미래 위험을 프롬프트 키워드로 예측 + 사후 grep 기반 증거로 봉합. 규칙 늘수록 튜닝 포인트만 증가
- 공통 해법: coverage 축소 → 남기는 3종(date_check/auth_diag/identifier_ref)만 **provider-contract** 형태로 재설계
- 판정: "전체 재설계"보다 "커버리지 축소 먼저"가 우선. 면적 줄이지 않으면 어떤 재설계도 과설계

### 상태 복원 축
- 공통 원인: 기억 상실 두려움 → SessionStart / PreCompact / PreToolUse 여러 층에서 TASKS/HANDOFF 덧대기
- 공통 해법: 복원은 SessionStart 한 곳, 저장은 PreCompact 한 곳. state_rebind_check는 detect-only
- evidence 축 줄이면 자동 경량화

### 진단/계측 축
- 공통 원인: 검증기와 관측기가 섞여 있고, 관측이 근사치인데 출력은 사실처럼 보임
- 공통 해법: smoke_fast / final_check → blocking / verifier. selfcheck / doctor_lite / hook_registry / gate_boundary_check → 관측·요약·lint. "더 많이 말하는 진단"이 아니라 "거짓 자신감 안 주는 진단"

### 게이트 경계 축
- 공통 원인: 경계는 좋아졌는데 최종 보증이 텍스트 grep tripwire에 기댐
- 공통 해법: grep → 시나리오 테스트로 승격. gate_boundary_check는 lint로만

## 축 간 의존
**evidence 선행**. evidence 수요 축소 없이는 나머지 축이 다 방어적으로 유지. 순서: evidence → diagnostics → state → boundary

## 7단계 실행 순서
1. hook_registry 정리/폐기 (list_active_hooks로 역할 흡수)
2. selfcheck 24h 정확 집계
3. doctor_lite 환경 의존 축소
4. evidence coverage 축소
5. 남긴 evidence 3종 contract형 재설계
6. state restore 경량화 (state_rebind detect-only 전환)
7. boundary 보증을 테스트로 승격

## 마무리
"더 똑똑한 evidence"가 아니라 "evidence가 덜 필요하도록 구조를 줄이기."
다음 라운드 제안: 1주차/2주차 작업묶음 + 검증 기준 + 롤백 조건 형태로 실행계획 문서 압축.
