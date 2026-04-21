# Round 3 — 최종 합의 (B5 3way 만장일치 통과)

## 판정 수령
- **GPT R3**: 통과 — "측정·차단 기준 분리와 Layer 1 분리 유지로 핵심 이의가 정리됐습니다"
- **Gemini R3**: 통과 — "측정(raw)과 차단(활성) 기준의 분리로 실무적 좌절감을 막고, M4 삭제를 통해 진단과 통제 레이어의 구조적 경계를 완벽하게 수호한 훌륭한 최종안"
- **pass_ratio = 2/2 = 1.0**

## 이전 라운드 요약
- R1: 양측 강력 비판 (Claude 원안 70%+ 수정 필요)
- R2: 종합안 — Gemini 통과, GPT 조건부(Q-Activate 세분화 + M4 invariant 제외)
- R3: 보정안 양측 통과

## 최종 채택 (양측 만장일치)

### 정책
- 실행 표면 정원제: hook 44(raw)→36(활성 목표) / command 30→25 / agent 9→12
- 지식 표면 TTL: skill 90일·memory 180일 미사용 archive 후보
- Glide Path: raw 시작 + 활성 목표 (혼합)
- 측정: raw + 활성 병행, 차단: 활성 기준
- 보호 레지스트리: `90_공통기준/protected_assets.yaml`

### 강제 메커니즘
- M1 advisory: `quota_advisory.sh` (PostToolUse Bash matcher, git commit 시 발동)
- M2 100% 도달 시 1 in 1 out 강제 (현재 활성 33 < 36 → 추가 가능, 36 도달 시 발동)
- M3 [bypass-quota] 태그 1회 면제 + 다음 정상 작업 2개 삭제 페널티
- M4 invariant 제외 (Layer 1 진단 시스템 분리 유지)

### 산출 알고리즘
1. 보호 제외 → 2. 고아 0순위 → 3. settings 미등록 → 4. 90일 무변경 → 5. 4등급 분류

### 4등급
- 삭제금지 / 병합후삭제 / 아카이브우선 / 즉시삭제후보

## Claude 자체 추가 의견 (사용자 "독립의견 유지" 지적 반영)

본 토론에서 양측 비판을 ~85% 수용. Claude 자체 의견 추가:

1. **Glide Path 속도**: "주 1~2개" Gemini 안 채택했으나 8주 너무 김. **월 1회 정리 세션 + 4~6개씩 감축 가능**으로 운영. yaml `glide_path: weekly_2_or_session_4` 명시.
2. **차단 기준 보강**: 활성 등록 hook만 차단하면 dead code 영원히 잔존. **즉시삭제후보(orphan) 4건 이상 누적 시 commit_gate 추가 경고**로 강제력 추가 권고 (B5 Phase 2 후속).

## 분리·후속 의제
- 본 의제 자체 종료 (B5 완료)
- B4 Self-Limiting → 다음 단계
