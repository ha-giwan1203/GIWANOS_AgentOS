# Round 2 — Claude 종합안 (4-way 대조)

> 비교: Claude 독자(round2_claude.md) + GPT(round2_gpt.md) + Gemini(round2_gemini.md)

## 합의 핵심
- **의제 3**: B 감지 ON / D 자동 진입 OFF 비대칭 (3자 모두 동의). C 강제 승격 보완.
- **의제 4**: R1~R5는 C 전용 + 반증형으로 재정의 (Claude 200자상한 → GPT/Gemini 반증형으로 발전). R5는 ERP/MES 잔존 데이터 + 논리적 롤백 필수.
- **의제 5**: 모든 응답 헤더 금지 + 선택 표기 (3자 동의). 표기 조건은 미세 조정 필요.
- **의제 6**: "이미 시작 + OR 조건" 기본 골격 합의. **건수 불일치 즉시 E**는 Gemini 이의 (입력 오류·필터링 가능성).

## 차별점 해소

### 차별점 1 — 의제 5 헤더 표기 조건
- **GPT**: B/C/D/E + ERP/MES 외부반영 포함 A
- **Gemini**: 모드 전환 시점(First Response) + 외부 데이터 쓰기 직전
- **Claude 종합**: **두 안 결합**.
  - 표기 조건 = (B/C/D/E 모드 응답) **OR** (ERP/MES 외부반영 포함 A) **OR** (모드 전환 발생)
  - 일반 A(엑셀 가공·보고서 작성)는 헤더 생략
  - Gemini 우려("B/C 판단 놓침")는 B/C가 이미 표기 대상이라 해소

### 차별점 2 — 의제 6 건수 불일치 처리
- **GPT**: 시간 무관 즉시 E
- **Gemini**: 입력 오류·필터링 차이(B/A 영역)일 수 있음, 과잉 판정 위험
- **Claude 종합**: **2단 판정**.
  - 1차: 건수 불일치 감지 → E 후보 + 사용자 1줄 경고("[E 후보: 건수 불일치 — 입력 오류 가능성 1차 점검 후 E 진입]")
  - 2차: 입력 오류·필터링이 명백히 아니면 E 진입. 명백한 단순 입력 오류면 A로 복귀.
  - **단, 외부 시스템에 이미 잔존 데이터가 남았으면 즉시 E** (Gemini 이의가 부정 못 함)

### 차별점 3 — 의제 6 시간 임계 vs 프로세스 고착
- **GPT**: 작업별 시간 임계 차등 (30/60초/+10분)
- **Gemini**: 시간보다 트랜잭션 생존·프로세스 고착 우선 (네트워크 지연 잦은 제조 환경 미스매치)
- **Claude 종합**: **AND 조합**. "시간 임계 초과 OR 프로세스 고착 발견" 둘 다 OR 조건에 추가. 시간 임계는 보수적(GPT 안 그대로) + 프로세스 고착(스케줄러 lock 잔존, OAuth redirect 무한 루프 등) 추가.

### 차별점 4 — 의제 4 R1~R5 구현 방법
- **GPT**: 반증형 질문 도입
- **Gemini**: Pre-commit hook 등 실제 코드 검증 연동
- **Claude 종합**: **현재는 GPT 반증형 채택, Gemini Pre-commit 연동은 별도 의제**. 이번 보정 범위(CLAUDE.md 1개 섹션)에서 hook 신설 금지. R1~R5는 plan 본문 체크리스트 + 반증 질문 형태. Pre-commit hook 신설은 향후 별건 의제로 TASKS.md 등록.

### 차별점 5 — Silent Update / 사용자 통제권
- **Gemini 제안**: C 강제 승격 시 'C모드 전환 필요' 경고 선행 → HANDOFF에 에스컬레이션 로그 강제
- **Claude 종합**: **채택**. C로 승격 시 응답 첫 줄에 명시적 헤더 (`[모드 전환: A → C / 사유: SKILL.md Step 절차 변경 감지 / 진행하려면 plan-first]`). HANDOFF 자동 갱신은 향후 의제(이번 범위 외).

### 차별점 6 — 마스터 정보(품번/공정코드) 불일치
- **Gemini 신규 제안**: 단순 건수 불일치 X, 마스터 정보 불일치 감지 시 즉시 E + B로 강제 이관
- **Claude 종합**: **채택**. 의제 6 OR 조건에 "마스터 정보(품번/공정코드/라인 매핑) 불일치 감지" 추가. 이 케이스는 입력 오류 가능성 거의 없음 → 즉시 E.

### 차별점 7 — Staging Table·PLC 인터치
- **Gemini 신규 제안**: ERP-E-01 (Staging 잔존 청소), MES PLC 인터치 타임아웃
- **Claude 종합**: **버림 (이번 범위 외)**. 본 보정은 CLAUDE.md 1개 섹션 추가가 한계. PLC/Staging은 도메인 CLAUDE.md(05_생산실적, 04_생산계획)에 별건 의제로 기록 필요.

## Round 2 최종 채택 항목 (§2 초안 보강)

1. ✅ **의제 3**: B 분류 감지 ON, D 자동 진입 OFF 비대칭. 시스템 파일 경로 수정 시 C 강제 승격(D 아님).
2. ✅ **의제 3 보강**: C 강제 승격 시 응답 첫 줄에 모드 전환 헤더 + 사용자 인지 라인.
3. ✅ **의제 4**: R1~R5는 C 전용. 반증 질문형으로 재정의.
4. ✅ **의제 4-R5**: ERP/MES/SmartMES/Z드라이브 잔존 데이터 + dry-run + 건수 확인 + 논리적 롤백 스크립트 필수 포함.
5. ✅ **의제 5**: 모든 응답 헤더 금지. 표기 조건 = B/C/D/E 모드 OR ERP/MES 외부반영 A OR 모드 전환 발생.
6. ✅ **의제 5 형식**: 1줄. `[모드: <코드> / 대상 또는 위험 / 다음 액션]`.
7. ✅ **의제 6 정량**: E 판정 = "이미 시작" AND ("시간 임계 초과(작업별 차등)" OR "외부 응답 부재" OR "잔존 데이터 위험" OR "입력 소스 충돌" OR "프로세스 고착(lock 잔존·redirect 루프)" OR "마스터 정보 불일치").
8. ✅ **의제 6 단순 건수 불일치 처리**: 1차 E 후보 + 1줄 경고 → 2차 진입(입력 오류 명백 아니면 E, 외부 잔존 데이터 있으면 즉시 E).
9. ⏳ **별건 의제로 등록 (이번 범위 외)**:
   - R1~R5 Pre-commit hook 연동
   - HANDOFF 자동 에스컬레이션 로그
   - PLC 인터치·Staging Table 잔존 청소

## claude_delta 측정
- Claude 초안 4의제 핵심 주장 vs 양측 본론:
  - 의제 3 "감지 ON/액션 OFF": GPT/Gemini 모두 채택 → none
  - 의제 4 "200자 상한": GPT의 반증형으로 발전됨 → partial
  - 의제 5 "도구 호출 트리거": GPT의 모드별 트리거로 대체 → major(폐기)
  - 의제 6 "OR 3조건": GPT가 1개 추가, Gemini가 2개 추가, Claude 종합이 6개로 확장 → partial(보강)
- **claude_delta**: `partial` (Claude 기여 일부 살아남음, 큰 부분은 양측 본론에서 발전)

## 자동 게이트 (양측 검증 받기 전 PENDING)
```json
{
  "cross_verification": {
    "gemini_verifies_gpt": {"verdict": "검증 필요", "reason": "건수 불일치 즉시 E는 입력 오류 가능성 배제 위험"},
    "gpt_verifies_gemini": {"verdict": "PENDING"},
    "gpt_verifies_claude": {"verdict": "PENDING"},
    "gemini_verifies_claude": {"verdict": "PENDING"},
    "issue_class": "B",
    "claude_delta": "partial",
    "skip_65": false,
    "round_count": 2
  }
}
```
