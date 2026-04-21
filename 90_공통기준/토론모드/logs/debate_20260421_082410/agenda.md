# 2자 토론 의제 (debate_20260421_082410)

- 모드: 2way (Claude × GPT)
- 의제: Case A — evidence_gate.sh GRACE_WINDOW 120 → 300 확장
- 분류: A (실행 흐름·판정 분기·차단 정책 전부 불변, 단일 상수 변경)
- 관련 보고서: `90_공통기준/업무관리/incident_improvement_20260421_session86.md`
- 선행 토론: `debate_20260420_143000_api_exception/round2_summary.md` (세션83 Round 2 4자 만장일치 "차단은 유지, 기록 중복만 억제 확장")

## 실측 근거 (보고서 기반 요약)
- 7일 evidence_gate 미해결 272건, 동일 fp 연속 간격 249샘플
- GRACE=120 억제 실제 18.5% (설계 대비 81.5% 놓침)
- 실측 median 347s, Top3 fp median 320~370s
- Top3 fp 7일 272건 중 194건(71%) 집중
- 증분 β 4건 반복 간격 119s·122s·135s·209s (GRACE 120 경계 직후 탈출)
- GRACE 300 확장 시 기대 억제율 46.2% (2.5배), GRACE 900 시 68.3% (3.7배)

## 조정안
- `.claude/hooks/evidence_gate.sh:59` `local GRACE_WINDOW=120` → `local GRACE_WINDOW=300`
- 주석 갱신 (세션86 실측 근거 추가)
- smoke_test 신규 섹션 50 (4건): 200s 억제 / 301s 기록 / 독립 fp 독립성 / 세션83 섹션 48 5건 회귀

## GPT에게 묻고 싶은 것
1. GRACE 120→300 확장의 역방향 리스크 (동일 fp 독립 이벤트 오억제)
2. 세션83 Round 2 합의(차단 유지, 기록만 억제) 경계 내 조정인지 확인
3. Case B(fingerprint 해시 입력 확장)·Case D(현행 유지)를 지금 같이 묶어야 할지, A 먼저 단독 적용 후 2주 관찰이 타당한지
4. smoke_test 4건 외에 추가 회귀 테스트 필요 여부
