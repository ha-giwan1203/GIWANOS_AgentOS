# Round 1 — Claude 종합 설계안

## 양측 교차 검증 결과
- `gemini_verifies_gpt`: 동의
- `gpt_verifies_gemini`: 동의
- pass_ratio (6-2/6-4만) = 2/2 = 1.0

## 통합 설계안 — SKILL.md Step 3-W에 추가할 "6-5 조건부 생략" 섹션

### 생략 조건 (모두 충족 필수)
**조건 A — 양측 무단서 동의**:
- 6-2 `gemini_verifies_gpt.verdict == "동의"` AND 6-4 `gpt_verifies_gemini.verdict == "동의"`
- 두 `reason` 문장에 조건부 단서 키워드 없음: "단, ...", "조건부", "추가 확인 필요", "다만", "하지만"

**조건 B — Claude 종합안 순수 축약**:
- 신규 정책/예외/분기/설계 문장 추가 없이 "채택/보류/버림 정리"만
- 양측 답변의 공통분모를 벗어나는 재해석·범위 확장·표현 변경 금지

**조건 C — 의제 성격**:
- 단순 판정형(A 분류 성격: 오타·값·버그·문서 정리·도메인 데이터)
- 구조·정책·프로토콜 변경(B 분류)이면 **무조건 6-5 유지**

### 시스템 제약 (기계 강제)
- `current_round === 1` 하드코딩 게이트. Round 2/3는 자동 생략 불가 (로직 비활성)
- 이유: Round 2/3은 불일치 누적 맥락이라 안전장치 제거 시 Claude 종합 오해 방지 실패

### JSON 스키마 확장
```json
{
  "cross_verification": {
    "gemini_verifies_gpt": {"verdict": "동의", "reason": "..."},
    "gpt_verifies_gemini": {"verdict": "동의", "reason": "..."},
    "pass_ratio_numeric": 1.0,
    "round_count": 1,
    "max_rounds": 3,
    "skip_65": true,
    "skip_65_reason": "양측 무단서 동의 + 순수 축약 + A 분류 + Round 1",
    "claude_delta": "none",
    "issue_class": "A"
  }
}
```

### 기록 의무
- 생략 시 `round{N}_claude_synthesis.md`에 `skip_65=true` 마킹 + `claude_delta` 상세 필드 보존
- 생략 여부 감사 가능하도록 JSON 로그에 네 필드(`skip_65`, `skip_65_reason`, `claude_delta`, `issue_class`) 필수

## Claude 종합 vs 양측 입장 — 재해석 자체 선언

**재해석 들어감 (claude_delta=partial)**:
- Gemini 제안 2개(하드코딩 게이트·조건 통폐합)를 GPT 5조건과 통합 재구성
- 조건 (2)에 "단서 키워드" 리스트 명시(원문엔 없음) → 범위 구체화
- JSON 스키마 예시 구체화(원문 필드명만 언급) → 운용 스펙 추가

**따라서 이번 Round 자체는 6-5 생략 불가**. 메타적으로 본 의제(6-5 생략 규정 신설)는 **프로토콜 변경 = B 분류 = 6-5 유지** 조건에 해당. 양측에 종합안 1줄 검증 요청 필수.
