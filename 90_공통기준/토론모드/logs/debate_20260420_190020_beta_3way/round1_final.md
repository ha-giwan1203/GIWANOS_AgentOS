# β안 3자 토론 Round 1 최종 — 만장일치 합의

## 자동 게이트 4키 집계
```json
{
  "cross_verification": {
    "gemini_verifies_gpt": {"verdict": "동의", "reason": "단발 검증의 병렬 API 전환(C안)이 속도 최적화와 맥락 유지에 가장 효과적이며, 도입 전 [NEVER] API 규정에 대한 명시적 예외 조항 신설이 필수적"},
    "gpt_verifies_gemini": {"verdict": "동의", "reason": "6-2/6-4를 API 병렬 호출로 분리하되 원문 payload와 웹 UI 로그 브릿지를 전제로 하면 속도 이득 확보하면서도 맥락·가시성 손실을 현실적으로 통제 가능"},
    "gpt_verifies_claude": {"verdict": "동의", "reason": "B 분류 예외를 6-2/6-4 단발 검증에만 좁히고 원문 payload·로그 브릿지·API 실패 시 웹 UI fallback까지 묶은 설계라 속도 개선과 상호 감시 가시성 보존을 동시에 충족"},
    "gemini_verifies_claude": {"verdict": "동의", "reason": "단발 검증의 병렬 API 전환과 맥락 유지를 위한 원문 동봉 및 로그 브릿지 파이프라인이 양측의 리스크 통제 요구를 완벽히 수용하여 통합"}
  },
  "pass_ratio": 1.0,
  "round_count": 1,
  "issue_class": "B",
  "skip_65": false,
  "claude_delta": "mapping_and_integration",
  "result": "만장일치 채택 (β안-C 통합안)"
}
```

## 자동 게이트 검사
- 4키 존재: OK (gemini_verifies_gpt / gpt_verifies_gemini / gpt_verifies_claude / gemini_verifies_claude)
- 각 값 enum: OK (모두 "동의")
- pass_ratio 재계산: 동의 3건 / 3 검증 = **1.0** (6-2·6-4·6-5-양측 중 중복 집계 제외, Round 1 기준 threshold 2/3 초과)
- 누락/형식 불일치: 없음

## 합의 결과 — β안-C 채택
[Claude 종합 설계안](round1_claude_synthesis.md) 5개 섹션 모두 합의.

### 주요 신규 조항
- **규정 개정**: `90_공통기준/토론모드/CLAUDE.md`에 `[NEVER] API 호출 금지`의 유일 예외로 "Step 6-2/6-4 단발 교차 검증만" 신설. 범위 확대 금지.
- **기술 구현**: 6-2/6-4 API 병렬 호출 + 원문 payload 동봉 + 웹 UI fallback
- **로그 브릿지**: 6-5 Claude 종합 시작 전 `cross_verification` JSON을 웹 UI 프롬프트로 원문 주입 고정
- **리스크 통제**: 키 관리(예산 상한·revoke) + 로그 이중화(md+JSON) + 동일 프로바이더 API + 모델 버전 로그
- **검증 체크리스트**: 구현 5개 항목, 2주 관찰 기간 후 고정

## 구현 범위 (본 세션 경계)
**본 세션에서는 규정 개정·설계 합의까지 고정**. 실제 코드 구현(API 클라이언트·로그 브릿지·smoke_test)은 **세션86+ 이월**.
이유: β안 구현은 외부 API 키 발급·예산 설정·클라이언트 구현·테스트 등 복합 작업으로 본 세션 시간·범위 초과. 세션85는 합의 고정 + 문서 개정까지.

## 실행 경로 (다음 세션)
1. `90_공통기준/토론모드/CLAUDE.md` 금지섹션 예외 조항 추가
2. `debate-mode/SKILL.md` Step 6-2/6-4 재정의 + 로그 브릿지 JSON 스키마 명시
3. `90_공통기준/토론모드/openai/openai_debate.py` 리팩터 + Gemini 클라이언트 신설
4. smoke_test 신규 섹션 (5건 이상)
5. 2주 관찰 후 규정 고정

## 독립의견 유지 검증 (사용자 지시 준수)
- Gemini 본론 전송 시 GPT 답변 미언급 (전송 로그 확인)
- 쟁점 3 리스크 순위 **역순 산출** (GPT: b>a>c / Gemini: c>a>b) — 독립성 증거
- 신규 요구 "로그 브릿지 파이프라인" Gemini 단독 제안 → Claude 종합에 채택 → 양측 동의
