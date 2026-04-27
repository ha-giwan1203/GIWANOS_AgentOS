# Round 1 — Claude 종합안 (4-way 대조 기반)

> 비교 대상: Claude 독자(round1_claude.md) + GPT 본론(round1_gpt.md) + Gemini 본론(round1_gemini.md)

## 합의된 사항 (3자 동의)
1. **기존 5종 유지** — 추가 모드 신설 0개. F. 메타작업 모드는 **버림** (Claude 초안 폐기).
2. **메타작업은 독립 모드 X** — Claude 초안의 F 모드 주장은 GPT/Gemini 양측 거부. 메타순환 위험.
3. **A↔C 경계** — 산출물 성격 + 영향 범위 기준. Claude·GPT·Gemini 모두 같은 방향(현장 결과물 vs 시스템 동작 변경).
4. **B↔E 경계** — "현재 실무/에이전트 가동 중단 여부"가 단일 기준.
5. **D 자동 승격 차단** — 사용자 명시 호출만.
6. **E는 최소 복구까지만** — 재발방지·구조 개선은 B/C로 분리.

## 차별점 (해소 필요)

### 차별점 1 — SKILL.md 처리
- **GPT**: `90_공통기준/스킬/*/SKILL.md` 수정은 **무조건 C** (시스템 동작 변경)
- **Gemini**: 실무 로직 '자산화' 과정인 SKILL.md 작성은 **A의 확장 여지**
- **Claude 종합안**: GPT 손을 들어준다. 이유는 (a) 본 저장소는 hook+skill+gate 결합도가 높아 SKILL.md 절차 변경이 실행 흐름·판정에 직결됨(현행 `feedback_structural_change_auto_three_way.md` "스킬 md의 Step 절차 분기 신설·삭제"가 B 분류로 이미 명시됨), (b) "자산화"라는 모호 개념을 도입하면 C 우회 통로가 생김. 단 Gemini 우려를 흡수해 **SKILL.md 안에 데이터·문구·주석·예시만 추가하는 변경은 A로 처리**(현행 자동승격 A 분류 "스킬 md의 주석·경고 문구·설명 추가"와 동치).

### 차별점 2 — 메타작업 처리 방식
- **GPT**: 보조 태그 3개 (리서치/학습, 상태정리, 회고/메타)
- **Gemini**: 각 모드의 Pre/Post Task 프로토콜로 강제 (DoD에 포함)
- **Claude 종합안**: **Gemini 안 채택**. 보조 태그는 분류만 늘리고 강제력 없음. Pre/Post Task로 모드 종료 조건에 포함시키면 누락 원천 차단. 구체화: 모든 모드 종료 시 **공통 Post Task** = "TASKS.md/STATUS.md/HANDOFF.md 갱신 필요 여부 1줄 선언"(현행 "## 종료 시 갱신" 절차 그대로). 회고는 별도 강제하지 않음(필요 시 사용자가 B/C로 호출).

### 차별점 3 — 우선순위 사다리
- **Claude 초안**: E > D > C > B > A > F
- **GPT**: 명시 > C(시스템 경로) > E > D > B > A
- **Gemini**: D > E > C > A > B
- **Claude 종합안**: GPT 안 베이스 + Gemini의 "E 우선" 원칙 흡수. 다음 사다리:
  ```
  1. 사용자 명시 지시 (모든 자동 사다리 위)
  2. E (현재 실무 차단 시 — Gemini "오염된 데이터" 논거 채택)
  3. C (시스템 파일 경로 수정 포함 시)
  4. D (사용자 명시 호출만 — 자동 승격 차단)
  5. B (분석)
  6. A (실무 산출물)
  ```
  - **차이점**: GPT가 D를 4번에 둔 것을 그대로 채택. Gemini가 D를 1번에 둔 것은 "사용자 명시 지시"와 동치이므로 1번으로 통합.
  - **A를 맨 아래에 두는 이유**: A는 "다른 모드가 활성 안 됐을 때의 기본값". 다른 모드 트리거가 없으면 A로 진행.

### 차별점 4 — System Health 하위 범주 (Gemini 신규 제안)
- **Gemini**: 외부 툴 연동·환경 설정 변경을 'System Health' 하위 범주로
- **Claude 종합안**: **버림**. 이유는 새 분류를 또 도입하면 메타순환. C 안에 흡수해서 처리. C 진입 시 R1~R5에 "외부 의존성 변경 여부" 항목이 이미 포함됨.

## 채택 결정

§2 초안에 반영할 보강 항목 (확정):
1. ✅ 5종 유지 (F 모드 신설 폐기)
2. ✅ A↔C: "현장 산출물 vs Claude Code 동작·규칙 변경" 기준 + 시스템 파일 경로 보호 목록 명시
3. ✅ B↔E: "현재 실무/에이전트 가동 중단 여부" 단일 기준
4. ✅ E 최소 복구 원칙 + 재발방지는 B/C 분리
5. ✅ D 자동 승격 차단 (사용자 명시 호출만)
6. ✅ 우선순위 사다리: 명시 > E > C > D > B > A
7. ✅ 메타작업 = Pre/Post Task 프로토콜 (Gemini 안)
8. ✅ SKILL.md 처리 — Step 절차 분기 변경은 C, 문구·주석·예시만 추가는 A (현행 B/A 분류 표 정합)

## claude_delta 측정
- Claude 초안 5개 주장 중:
  - 주장 1 (F 모드 신설): **버림** (양측 거부)
  - 주장 2 (A↔C 수신자 기준): **채택** (양측 동의, 표현만 정련)
  - 주장 3 (B↔E 시간축): **채택** (양측 동의)
  - 주장 4 (사다리): **부분 채택** (E·D 위치 조정)
  - 주장 5 (헤더 비대칭화): **양측 미언급** → Round 2 의제 5에서 본격 다룸
- **claude_delta**: `partial` (Claude 기여 일부 반영, 절반 폐기)

## 자동 게이트 4키 (다음 단계 양측 검증 후 채워질 필드)

```json
{
  "cross_verification": {
    "gemini_verifies_gpt": {"verdict": "검증 필요", "reason": "SKILL.md 무조건 C 고정은 실무 자동화 자산화와 충돌 소지"},
    "gpt_verifies_gemini": {"verdict": "PENDING", "reason": "다음 메시지에서 수령"},
    "gpt_verifies_claude": {"verdict": "PENDING", "reason": "다음 메시지에서 수령"},
    "gemini_verifies_claude": {"verdict": "PENDING", "reason": "다음 메시지에서 수령"},
    "issue_class": "B",
    "claude_delta": "partial",
    "skip_65": false,
    "round_count": 1
  }
}
```
