# Round 1 — GPT 최종 판정 (2026-04-23 debate_20260423_193314)

## 종합
- 3자 자동 승격 불필요 (A안/C2 수렴)
- 의제1 A안 채택 + M4 선행 조건부 동의
- 의제2 C2 채택
- 의제3 수정 채택 (URL/숫자 제거, dry-run만 통합)

## 의제1 (SessionStart 정책 + parse_helpers)
**채택 — A안**
- 분류: 실증됨
- 근거: DESIGN_PRINCIPLES.md:10 "정적 출력만" vs 실물 session_start_restore.sh는 smoke_fast/doctor_lite/token_threshold_check/drift/selfcheck/incident 전부 수행
- 반박 B안: 과수술. advisory visibility 손실 큼. doctor_lite도 경량 advisory
- 문구 수정 방향: "정적 + advisory 보조 허용"

**채택 — parse_helpers M4 선행, 단 M3 즉시 후속 조건**
- 분류: 실증됨
- 근거: risk_profile_prompt.sh가 DOMAIN_REGISTRY 셸 파싱 중. parse_helpers는 이미 공통 파서 계층 존재
- **반박**: M4만 하고 M3 미루는 것 반대. final_check.sh도 registered_hook_names/readme_active_hook_count/status_hook_count 자체 파싱 → SSoT 미완. 최종 입장: **M4 선행 가능, M3 지연 불가**

## 의제2 (도메인 STATUS drift)
**채택 — C2** (신규 advisory 훅 → 실측 후 gate 승격)
- 분류: 실증됨
- 근거: 직접 대조 — 02/04/06 2026-04-11, 05 2026-04-06, 10 2026-03-31. final_check.sh는 전역 STATUS만 동기화
- 반박 C1: final_check 과적재 (이미 훅/문서/세션 drift 담당). 1 Problem ↔ 1 Hook 위반
- 반박 C3: finish는 종료 시점만, 세션 중간 drift 가시성 없음

## 의제3 (permissions 정리)
**수정 채택 — URL echo/숫자 echo 제거, dry-run만 통합**
- 분류: 실증됨
- 근거: settings.json에 이미 `Bash(echo:*)` 포괄 존재. settings.local.json URL/숫자 1회용은 "포괄 있으면 1회용 금지" 원칙 정면충돌 (CLAUDE.md 5단계 의사결정 트리)
- 반박: local에 새 포괄 추가는 중복. URL·숫자는 제거. dry-run은 같은 스크립트 계열이라 범용 패턴으로 묶기

## GPT 자기 평가 수정
- #4 permissions 부채: 규모 과대 평가 인정, 110→63 반감 진전 인정
- #6 post_commit_notify: "배치 오류" → "README 분류/표기 문제"로 재해석. Claude의 이동+event 명시 반영 방향 인정

## Claude 하네스 분석
- 채택 3건 (의제1 A안, 의제2 C2, 의제3 수정)
- 조건부 1건 (M4 후 M3 즉시 후속 — GPT 조건 수용)
- 버림 0건 (GPT 원래 5순위 incident_repair 경계 재정의는 Claude가 버림 선언 → GPT 수용)
- 3자 승격 판단: **불필요** (수렴 충분)
