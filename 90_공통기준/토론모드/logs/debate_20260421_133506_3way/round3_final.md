# Round 3 — 최종 합의 (3way 만장일치 통과)

## 판정 수령

**GPT**: 통과
> "M3를 gate로 올린 점과 D2를 30일 유예+표본하한+하한선으로 묶은 보정이 핵심 우려를 해소합니다."

**Gemini**: 통과
> "GPT가 지적한 M3 게이트 격상과 D2 하이브리드(30일 유예+최소표본+하한선) 안전장치가 완벽히 결합. UX 보호를 위한 프로젝트성 범위 제한도 타당."

## pass_ratio
- 양측 웹 UI 최종판정 "통과" 2/2 → **pass_ratio = 1.0**
- round_count = 3 (R1 cross 부분동의 → R2 GPT 조건부 → R3 양측 통과). max_rounds=3 이내 수렴.

## 최종 채택안 (요약)

### Invariants 8개
1. `notion_last_sync_age < 24h` — read-only API 즉시 평가 + 5s timeout
2. `mes_last_upload_age < 영업일7` — last_ok 무접촉 판정
3. `uncommitted_changes_age < 24h` — Git 원본주의 (Gemini 신규)
4. `incident_unresolved < 100` — 디바운스 N=3회
5. `smoke_test = ALL PASS`
6. `TASKS.md_lines < 800`
7. `session_kernel_age < 24h`
8. `settings_drift = none` (GPT 신규)

### 정책 5개
- P1 Layer 1은 감지만, 자동 조치 절대 금지
- P2 SessionStart 1회 + 1세션 캐시 + 재계산 금지
- P3 OS timeout 5s + Depth/Retry 제한 + WARN(Timeout) 격리
- P4 평가 결과는 요약 1건만 incident 기록, 세부 별도 JSON
- P5 디바운스 N=3회

### 강제 메커니즘 4개
- M1 SessionStart hook → `[System Health]` stdout 출력 (Claude 컨텍스트 강제 주입)
- M2 CLAUDE.md 조항: Claude 첫 메시지 health summary 1줄 의무
- M3 **gate**: UserPromptSubmit hook이 누락 감지 시 stderr 경고 + 보강 프롬프트 자동 주입
- M4 단순 인사·확인 감지 시 면제

### D2 정책 (3중 안전장치)
- 첫 30일: 하드코딩 임계값만
- 30일 후: 표본 ≥ 30 + p95 산출 활성, 미충족 시 하드코딩 fallback
- 표본 충족 후에도 하드코딩 하한선 강제

### Q-Range
- 매 SessionStart 1회 + 첫 사용자 응답 시 출력
- 단순 인사("안녕"·"테스트")·단발 확인 면제
- 프로젝트성 작업(/finish, /debate-mode, /settlement, 도메인 키워드) 진입 시 강제

## 분리된 의제
- **B5 Subtraction Quota** 신설 — invariant #12 (hook≤36) 별도 토론

## 구현 착수
다음 단계: Layer 1 구현 (invariants.yaml + diagnose.py + HEALTH.md + SessionStart hook + CLAUDE.md 조항 + UserPromptSubmit gate). 완료 후 `[3way]` 태그 커밋 + push + 양측 최종 검증.
