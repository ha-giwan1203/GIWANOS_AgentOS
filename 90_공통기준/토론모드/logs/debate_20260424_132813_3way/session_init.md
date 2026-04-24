# 3자 토론 세션 초기화 — 세션102

- **session_id**: debate_20260424_132813_3way
- **mode**: 3way (Gemini API 대체 — 사용자 지시 예외)
- **선례**: 세션101 "Gemini API 대체" 패턴 동일 적용
- **의제**: 세션101 GPT 평가 후속 — auto_commit_state.sh 운영 계약 보강
- **분류**: B (hook 실행 흐름 영향 — hook_common wrapper 적용)
- **max_rounds**: 3

## 협의 안건 (4건)
1. P-1: auto_commit_state.sh를 protected_assets.yaml 등록 (위치: Stop 계열 vs 별도)
2. P-2: README Failure Contract 표에 추가 (advisory + final_check fail시 push 중단 계약)
3. hook_common wrapper 적용 (`hook_advisory` 래핑 — exit 0 + timing/incident 기록만 추가)
4. 커밋 묶음 전략: 3건 단일 [3way] 커밋 vs 분리

## Claude 사전 입장
- 3건 묶음 (단일 목적: auto_commit_state 운영 계약 보강)
- hook_common wrapper는 `hook_advisory` 사용 (push 흐름 불변, 계측만 추가)

## 도구 운용
- GPT: 웹 UI 멀티턴 (`/gpt-send` + `/gpt-read`)
- Gemini: API (`/ask-gemini` CLI 단발) — 사용자 지시 예외
