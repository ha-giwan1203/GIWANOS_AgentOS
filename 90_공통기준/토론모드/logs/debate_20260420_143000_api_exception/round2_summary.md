# A 의제 Round 2 — 3자 API 토론 (세션83 사용자 명시 예외)

- 일시: 2026-04-20 14:15~14:27 KST
- 예외 경로: 토론모드 `[NEVER] API 호출` 규정을 **이번 세션만** 사용자 승인 하에 완화
- 정식 토론모드 로그(`logs/debate_*_3way`)와 분리 저장
- 사용 API: Gemini 2.5-pro (thinking), GPT-5.2 (2025-12-11), GPT o4-mini (2025-04-16 reasoning)
- 진짜 API 3자 (Claude + GPT × 2 + Gemini × 2) 교차 검증 방식

## 입력 데이터

B 분석 결과 (`90_공통기준/업무관리/evidence_gate_20260419_analysis.md`):
- 7일 evidence_missing 332건, 04-19 = 165건(49.7%), 전원 resolved:false
- 04-19 01:06~01:53 KST 47분간 42건 연속 발화
- fingerprint 상위 3종 180/272 = 66% 집중
- 코드 대조: `session_start_restore.sh:14-20`, `evidence_gate.sh:117-121`, `evidence_mark_read.sh:104-105`, `skill_instruction_gate.sh:39,65`

## Round 2 판정 매트릭스

| 문항 | Gemini 2.5-pro | GPT o4-mini (reasoning) | GPT-5.2 | Claude 종합 |
|------|---------------|------------------------|---------|------------|
| Q1 (α 원인) | Claude 가설 채택 / 실증됨 | 버림(Gemini-flash) → Claude 채택 / 실증됨 | 채택 / 실증됨 | **Claude 가설(반복 commit 흐름) 채택, 3자 만장일치** |
| Q2 (γ self-throttle) | (A) 채택 / 일반론 | 채택(A) / 실증됨 | 채택(A), 버림(B) / 실증됨 | **(A) 차단 유지+incident 중복 억제만, 3자 만장일치** |
| Q3 (δ 스코프) | 별건 분리 / 환경미스매치 | 채택(별건 분리) / 실증됨 | 보류(별건 분리 권고) / 구현경로미정 | **별건 분리, 3자 합의 성립** |

pass_ratio: Q1 3/3, Q2 3/3, Q3 3/3 → Round 2 전건 PASS.

## 조치 합의 (구현 대상)

1. **evidence_gate.sh fingerprint self-throttle**: 동일 fingerprint가 60초 이내 재발화 시 ledger 중복 기록 억제 + stderr warn. **차단 자체는 유지**.
   - 구현 위치: `log_incident()` 호출 직전 (deny 직전 블록)
   - 상태 파일: `.claude/state/evidence_gate_fp_cache.txt` (fp=timestamp KV)
   - 만료: 60초 기준, 다음 호출 시 자동 정리

2. **smoke_test 2건 추가**:
   - 동일 fp 60초 내 재발화 → ledger에 1건만 기록 + deny는 유지
   - 만료 후 재발화 → ledger에 신규 기록

3. **δ 별건 분리**: skill_instruction_gate 36건은 TASKS.md 세션83+ 이월 안건으로 별건 등록 (본 토론 범위 밖)

4. **Gemini-flash Round 2의 역방향 조치 (fresh_ok 완화·cooldown 중 차단 생략)는 버림** — 세션78 smoke_test 안전망과 충돌, gate 본질 훼손

## 외부 모델별 원문

- `a_round2_gpt_20260420_142529.json` (o4-mini)
- `a_round2_gpt52_20260420_142746.json` (gpt-5.2)
- Gemini 2.5-pro stdout 응답 (본 디렉토리 `gemini_pro_round2.md`)
- Gemini 2.5-flash 초기 응답 (Claude 실측 대조 후 일부 버림)

## 판정 요약 1줄

- 채택 3건 / 보류 0건 / 버림 2건 (Gemini-flash 역방향 조치 2종)
