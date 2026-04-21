# Agenda — B1: Self-X Layer 1 (Self-Detection) 도입

**의제**: invariants.yaml 기반 자가 진단 + Claude 첫 메시지 health summary 의무화
**모드**: 3자 토론 (Claude × GPT × Gemini), 상호 감시 프로토콜
**B 분류 근거**: hook 신설 + CLAUDE.md "첫 메시지 health summary 의무" 조항 추가 = 실행 흐름 변경
**β안-C 적용**: Step 6-2/6-4 단발 교차검증 (정량 임계값 결정 위험)

## 배경

- 세션86 Notion 동기화 41세션 미인지 사건. 시스템이 사용자가 묻기 전엔 침묵
- 사용자 본인 진단: "내가 일일이 모든 사항을 알 수 없다" / "어디 고장났는지 모르겠다"
- 플랜: `C:\Users\User\.claude\plans\wobbly-prancing-forest.md` 4-Layer 구조 중 Layer 1
- 선행 정리 완료: incident_ledger 미해결 954→469건 (커밋 9cb8e740)

## 핵심 결정 사항 (5건)

### D1. invariant 항목 수
- ① 최소 8개 (핵심만)
- ② 중간 12~15개 (도메인 포함)
- ③ 전체 20+ (포괄)

### D2. 임계값 설정 방식
- ① 정량 하드코딩 (yaml에 숫자 직접)
- ② 데이터 기반 자동 산출 (최근 30일 분포의 p95)
- ③ 혼합 (안전 임계값은 하드코딩, 추세 임계값은 자동)

### D3. 첫 메시지 보고 형식
- ① 1줄 압축: `[health] 12 OK · 2 WARN · 1 CRITICAL`
- ② 다행 상세: 각 항목 1줄씩
- ③ 조건부: 정상은 1줄, WARN/CRITICAL만 추가 라인

### D4. 외부 시스템 timeout 처리
- ① cached health TTL 1h
- ② cached health TTL 24h + 강제 refresh 명령
- ③ 즉시 평가 + 5초 timeout fallback

### D5. 새 incident 클래스 invariant 자동 추가
- ① 자동 추가 (3회 이상 발생 시)
- ② 수동 토론 게이트 (Claude가 후보 제안, 사용자 승인)
- ③ 하이브리드 (T2 1-click — 1초 승인)

## 후보 invariants (12개 — 검토 대상)

| # | invariant | 근거 |
|---|-----------|------|
| 1 | notion_last_sync_age < 24h | 세션86 사건 직접 박제 |
| 2 | mes_last_upload_age < 영업일7 | MES 미업로드 사고 예방 |
| 3 | incident_unresolved < 100 | 학습루프 부담 상한 |
| 4 | smoke_test = ALL PASS | 기존 자산 활용 |
| 5 | TASKS.md_lines < 800 | 기존 token_threshold |
| 6 | session_kernel_age < 24h | session_start 이미 fallback |
| 7 | hook_avg_latency < 2s | 응답성 보호 |
| 8 | 정산 파이프라인 last_run.success | 도메인 무결성 |
| 9 | 라인배치 매핑 정합성 OK | 도메인 무결성 |
| 10 | 외부 API 키 만료 > 30d | 토큰·키 사고 예방 |
| 11 | 디스크 사용량·.bak 크기 | 운영 누적 방지 |
| 12 | hook 수 ≤ 36 (현재) | Subtraction Quota 시동 |

---

## Claude 독립 의견 (먼저 제시, GPT/Gemini는 검증·반박)

> 본 의견은 GPT/Gemini 응답을 받기 전에 작성. 외부 모델 의견은 하네스 라벨(실증됨·일반론·환경미스매치·메타순환·구현경로미정·과잉설계)로 분류 후 채택/보류/버림 판정한다.

### D1: **②중간 (12개)** 선택
- ①최소 8개는 도메인 invariant(정산·라인배치) 누락 → "고장 미인지" 본질 문제 미해결
- ③전체 20+는 초기 1세션에 과잉 설계, 임계값 검증 부담 큼
- 12개로 시작 후 D5 메커니즘으로 점진 확장

### D2: **③혼합** 선택
- ①하드코딩만은 데이터 변화 시 매번 토론 필요 → 운영 부담 재발
- ②자동 산출만은 본 저장소 데이터셋 작아(7일 분포) p95 불안정
- 혼합: 안전 임계값(notion 24h, smoke PASS 등)은 하드코딩, 추세 임계값(latency·incident 카운트)은 자동 산출 + 하한선 강제

### D3: **③조건부** 선택
- ①1줄만은 사용자가 상세 확인하려면 별도 명령 필요 → 보고 의무 무용지물
- ②다행은 매 응답에 12줄 차지 → 컨텍스트·토큰 낭비
- 조건부: 정상 1줄(`[health] 12 OK`), WARN/CRITICAL은 자동 펼침. 평소 1줄, 사고 시 즉시 가시

### D4: **③즉시 평가 + 5초 timeout** 선택 (보수 수정)
- 외부 시스템 응답 자체가 health 신호. cache는 silent failure 위험 (세션86 사건 재발 가능성)
- ②24h cache는 너무 길음. ①1h도 사고 1시간 누적
- 단: timeout fallback 시 "stale check (last_ok=N분전)" 명시. 침묵 금지

### D5: **③하이브리드 (T2 1-click)** 선택
- ①자동 추가는 invariant 폭주 위험 (Layer 4 미도입 단계라 위험 큼)
- ②수동 토론 게이트는 매번 토론 → 운영 부담 재발 (Self-X 도입 취지 위반)
- T2 1-click: Claude가 후보 제안 → 사용자 1초 y/n. B4(Layer 4) 도입 후 자동 추가 검토

### 추가 의견 — invariant #12 (hook 수 ≤ 36)
- "Subtraction Quota 시동"으로 표시했으나, 본 토론에서 정식 채택 권고
- 현재 hook 36개 = 상한. 신규 추가 = 기존 1개 제거 강제
- B 분류 별도 의제로 다룰지, B1에 포함할지 토론 필요

### 위험 식별
- **메타루프 위험**: invariant 평가 자체가 hook이면 hook이 hook을 평가 → Layer 4(circuit breaker) 미도입 상태에서 무한 평가 가능. SessionStart 1회만 실행, 결과 캐싱 필수
- **첫 메시지 의무 위반 추적 불가**: Claude가 health summary 누락해도 게이트 없음 → CLAUDE.md 조항만으로 충분한지 검증 필요
- **외부 시스템 평가의 부작용**: MES/ERP에 ping 보내면 ERP 부하·로그 오염. read-only 평가 경로 확인 필수

---

## 양측에 묻는 핵심 질문

1. D1~D5 각 결정에 동의/이의/추가 안?
2. 12개 invariant 후보 중 빠진 것·과한 것 1~2개?
3. **메타루프 위험**(invariant 평가 hook이 폭주) 차단 방안?
4. **첫 메시지 health summary 의무**의 강제 메커니즘 (CLAUDE.md 조항만으로 충분한가, 별도 hook 필요한가)?
5. invariant #12 (Subtraction Quota)는 B1 포함 vs 별도 의제 분리?

응답 형식: 각 결정·질문에 대해 1~3문장. 한국어만. 추가 위험 식별 환영.

---

## 토론 절차
- Round 1: GPT·Gemini 독립 의견 (각자 의제 본론)
- Round 1.5: β안-C 단발 교차검증 (양측이 상대 의견 1줄 검증)
- Round 2: Claude 종합 + 양측 검증
- Round 3: 합의 또는 재라운드 (max 3회)
- pass_ratio ≥ 2/3 시 채택
