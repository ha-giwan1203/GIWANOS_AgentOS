# Round 1 — GPT 본론 (Step 6-1)

수신: 2026-04-29 ~07:58 KST
모델: gpt-5-5-thinking

## 핵심 판정
- (a) 보류 — DOM 의존
- (b) 버림 — 단독 무효
- (c) 보류 — 과설계
- (d) 채택 통과 — 오늘 수동 복구와 동일

## (d) 권장 흐름
```
_wait_oauth_complete 30초 실패
→ 현재 URL이 auth-dev이고 /login이 아님
→ _safe_goto(page, D0_URL) 1회
→ _wait_oauth_complete 재대기
→ 그래도 실패하면 기존 RuntimeError
```

## 예외 처리 가이드
- _safe_goto(D0_URL) 후에도 URL이 계속 auth-dev → 실패 처리
- /login?error 복귀 → 기존 로그인 재시도 흐름
- 약관 동의·권한 부족·타 클라이언트 강제 선택 → DOM 자동 클릭 금지, 실패 처리. 이유: 잘못된 클라이언트/권한 상태 자동 넘기면 잔존 데이터 위험

## 실패 메시지 구체화 권고
> "OAuth 완료 실패: auth-dev 클라이언트 선택 화면에서 D0_URL 직접 이동 1회 시도 후에도 erp-dev 미도달"
- "로그인 실패"로 뭉개지 말 것

## (d)+(b) 의견
- (d) 단독 채택. (b) 보강 불필요
- 본질이 erp-dev 탭 부재인데 (b)는 보조 필터라 첫 실패 해결력 약함
- (b) 추가 시 탭 선택 정책 복잡화
- Day 2+ 같은 사고가 erp-dev 탭 보유 상태에서 재발하면 그때 (b) 별도 보강

## R1~R5 답변
- R1: `_wait_oauth_complete` 실패 후 URL이 /login 아니면 즉시 실패하는 분기. 클라이언트 선택 화면은 /login 아니지만 D0 URL 직접 이동으로 복구 가능
- R2: `navigate_to_d0` OAuth 실패 분기 일부만. 업로드·엑셀·selectList·multiList 영향 없음
- R3: ensure_erp_login·_wait_oauth_complete·_safe_goto·navigate_to_d0 주변. 새 DOM/새 탭 정책 추가 없음
- R4: 오늘 수동 복구 (playwright CDP auth-dev → D0 URL goto, 14건 등록 완료)
- R5: 3줄 수준, 등록 전 단계 중단. ERP/MES 잔존 위험 낮음. 롤백은 분기 제거

## 최종 결론
(d) 단독 채택 + 실패 메시지 구체화 필수
