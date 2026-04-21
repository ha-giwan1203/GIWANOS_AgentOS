# Round 1 Claude 종합안 (6-5)

> 양측 우려 흡수 후 종합. 라벨: 실증됨 / 일반론 / 환경미스매치 / 메타순환 / 구현경로미정 / 과잉설계
> cross_verification: Gemini→GPT 동의, GPT→Gemini 검증 필요(D4·D5 우려) → 6-5 종합 필수

## 하네스 분석 (양측 의견)

### 채택 (실증됨)
1. **D1 12개 → 축소** (Gemini 5~6 / GPT 8~10): 양측 공통, 도메인 깊은 정합성 항목 제외 → **8개로 결정** (중간값)
2. **D4 외부 시스템 cache 우선**: Gemini "비동기 크론 + 상태 파일 즉시 읽기 + 갱신 시각 표시", GPT "Notion read-only는 즉시, MES/ERP는 last_ok 무접촉" — **하이브리드 채택** (Notion=즉시 timeout 5s, MES/ERP=last_ok 무접촉, 양측 갱신시각 표시)
3. **Q4 별도 메커니즘 필수** (CLAUDE.md만 부족): Gemini "쉘이 [System Health] 블록 stdout 출력", GPT "전용 응답 훅 없음" — **쉘 출력 + UserPromptSubmit hook 보조** 채택
4. **Q5 invariant #12 (hook≤36) B1 분리**: 양측 공통 → **별도 의제(B5 Subtraction Quota) 신설**
5. **Q3 메타루프 격리**: GPT "SessionStart 1회 + 1세션 캐시 + 요약 1건만 기록", Gemini "Depth/Retry 제한 + OS timeout" — **양측 통합 채택**
6. **Q2 신규 invariant**: Gemini "uncommitted_changes_age", GPT "settings drift + last_ok timestamp" — **모두 추가**
7. **D3 WARN 3줄 / CRITICAL 상세** (GPT 보강): 채택
8. **D5 7일 3회 + 영향도 충족 시만 승격** (GPT 강화): 채택 — **D5 ① 즉시 1-click 폐기**
9. **추가 위험: Layer 1은 감지만, 자동 조치 절대 금지** (GPT): 채택 — 종합안 명문화
10. **추가 위험: Alert Fatigue 디바운스 N=3회** (Gemini): 채택

### 보류 (한쪽 강조, 추가 검증 필요)
- **D2 30일 하드코딩 유예** (Gemini): GPT는 즉시 혼합 동의 — Round 2 종합에서 결정. 우선 30일 유예 후 동적 산출 활성 안 채택
- **Health summary 범위 "프로젝트성 작업 시작 시"** (GPT): "세션 첫 메시지" 강제는 단순 질문 시 UX 망가짐 — Round 2에서 트리거 조건 정의 필요. 잠정: 매 SessionStart + 첫 사용자 응답 시 1줄, 비프로젝트성(인사·확인) 감지 시 생략

### 버림
- 없음

### 환경 미스매치 / 과잉 설계
- 없음 (양측 모두 본 저장소 환경 정합)

## 종합 채택안 (8 invariants + 5 정책)

### Invariants (8개)
1. `notion_last_sync_age < 24h` — read-only API 즉시 평가 + 5s timeout, 실패 시 last_ok 표시
2. `mes_last_upload_age < 영업일7` — last_ok 무접촉 판정, 갱신 시각 표시
3. `uncommitted_changes_age < 24h` — Git 원본주의 (Gemini 신규)
4. `incident_unresolved < 100` — 디바운스 N=3회 적용
5. `smoke_test = ALL PASS` — 기존 자산 활용
6. `TASKS.md_lines < 800` — 기존 token_threshold
7. `session_kernel_age < 24h` — SessionStart fallback 연계
8. `settings_drift = none` — settings.json·hooks/README·STATUS hook 수 정합 (GPT 신규)

### 정책 (5개)
- **P1**: Layer 1은 감지만. 자동 조치 절대 금지 (Layer 2/3 도입 전)
- **P2**: SessionStart 1회 실행 + 1세션 캐시 + 동일 세션 재계산 금지
- **P3**: 평가 스크립트 OS timeout 5s + Depth/Retry 제한 + 시간 초과 시 즉시 WARN(Timeout) 격리
- **P4**: invariant 평가 결과는 "요약 1건만 incident 기록", 세부는 별도 JSON (`.claude/self/last_diagnosis.json`)
- **P5**: 디바운스 N=3회 — 연속 3회 실패 시만 WARN/CRITICAL 격상

### 강제 메커니즘
- **M1**: SessionStart hook이 invariant 평가 → `.claude/self/HEALTH.md` 1페이지 출력 + 1줄 요약을 stdout 첫 줄에 출력 (Claude 컨텍스트 강제 주입)
- **M2**: CLAUDE.md 조항 추가: "Claude 첫 메시지에 health summary 1줄 의무 (단순 인사·확인 제외)"
- **M3**: UserPromptSubmit hook이 첫 사용자 메시지에 health summary 누락 감지 시 advisory log

### 분리된 의제 (별도 토론)
- **B5 Subtraction Quota**: hook 수 ≤ 36, skill 수 ≤ 50, memory entry 수 ≤ 30 등 구조 통제 정책

## D2·Health summary 범위 결정 (양측 검증 요청)

본 종합안의 미해결 2건에 양측 답 요청 (Round 2 step):

**Q-D2**: 첫 30일 하드코딩만 vs 즉시 혼합 — 어느 쪽?
**Q-Range**: health summary 트리거 — 매 SessionStart + 첫 응답 1회 vs "프로젝트성 작업"만 vs 모든 응답?

## 검증 요청
"통과 / 조건부 통과 / 실패" 중 하나. 한국어 200자 내외. Q-D2·Q-Range 답 포함.
