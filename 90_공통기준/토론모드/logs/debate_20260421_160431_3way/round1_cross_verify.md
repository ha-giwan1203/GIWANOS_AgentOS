# Round 1 — 교차 검증 (6-2/6-4/6-5 통합)

## 6-2: Gemini → GPT 1줄 검증 (생략, 단문 Round 1에서 단일 왕복으로 처리)

## 6-4: GPT → Gemini 1줄 검증 (생략, 동일 사유)

## 6-5: Claude 종합안 → 양측 최종 검증

### GPT 6-5 응답
verdict: **검증필요**
근거: 6번 YAML 프론트매터는 TASKS 원본 안정성 해칠 수 있음
추가조건: 6번은 별도 `notion_snapshot.yaml/json` 생성으로 대체하면 동의

### Gemini 6-5 응답
verdict: **동의**
근거: 마커 유실 등 예외 상황을 완벽히 방어하며 멱등성을 보장하는 견고한 아키텍처
추가조건: 없음

### Claude 조건 수용 판단
- TASKS.md는 Claude·사용자 빈번 편집 대상. YAML 프론트매터 삽입은 기존 md 파싱 경로에 회귀 리스크
- 별도 `notion_snapshot.json` 파일은 단일 책임 원칙에 부합 (notion_sync 전용 중간 산출물)
- 생성 타이밍: finish 9단계 직전 또는 auto-commit 후 hook에서
- **GPT 조건 수용, 항목 6 수정**

## 최종 합의안 (수정 반영)

### 구현 7묶음 (항목 6 수정됨)
1. SYNC_START/END marker 블록 (STATUS 상단 고정, 내부만 재생성)
2. `position.after_block` API 전환 (deprecated `after` 제거)
3. 페이지 제목 세션 경계만 갱신 (매 커밋 X)
4. 제목 실패 검증 로그 승격 (best-effort 조용한 실패 제거)
5. generated block "편집 금지" 경고 헤더
6. **`notion_snapshot.json` 별도 파일 생성 (TASKS.md 최상단 10줄 복제 대신 — GPT 조건 수용)**
7. 마커 수동 삭제 시 자동 재생성 fallback

## JSON 스키마

```json
{
  "cross_verification": {
    "gpt_verifies_claude": {"verdict": "검증필요→동의(조건 수용)", "reason": "6번 별도 파일 분리 시 동의"},
    "gemini_verifies_claude": {"verdict": "동의", "reason": "마커 유실 방어 + 멱등성"},
    "pass_ratio_numeric": 1.0,
    "round_count": 1,
    "max_rounds": 3,
    "skip_65": false,
    "skip_65_reason": null,
    "claude_delta": "partial",
    "issue_class": "B"
  }
}
```

## pass_ratio = 3/3 = 1.0 (조건 수용 반영 후)

## 다음 단계
1. Step 4b critic-reviewer 1회 호출 (필수)
2. 통과 시 Step 5 구현 진입
