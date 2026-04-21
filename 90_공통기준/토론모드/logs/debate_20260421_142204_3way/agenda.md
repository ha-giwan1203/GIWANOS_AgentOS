# Agenda — B5: Subtraction Quota (구조 통제 정원제)

**의제**: 추가 = 제거 강제. hook/skill/memory/command/agent 정원 상한 + 위반 시 차단·경고
**모드**: 3자 토론, 상호 감시 프로토콜
**B 분류 근거**: 신규 hook(quota gate) + commit_gate 흐름 변경 + 신설 정책

## 배경

- B1 토론에서 양측 합의로 분리됨 (Self-Limiting 철학, Layer 2/4 영역)
- 사용자 본인 진단 "운영 너무 힘들다" 본질 — 모든 문제를 "추가"로 해결한 누적 결과
- B1 invariant_drift 평가에서 settings(31) vs files(44) 11개 갭 노출

## 실측 (2026-04-21)

| 카테고리 | 현재 | 추정 임계 (B1 토론) | 초과 |
|---------|------|---------------------|------|
| hook (.sh) | 44 | 36 | +8 |
| skill (SKILL.md+.skill) | 38 | 50 | -12 (여유) |
| memory entry | 38 | 30 | +8 |
| command | 30 | (미정) | ? |
| agent | 9 | (미정) | ? |

## 핵심 결정 사항 (5건)

### D1. 카테고리 범위
- ① 핵심 3개 (hook/skill/memory)
- ② 5개 전체 (hook/skill/memory/command/agent)
- ③ 카테고리 확장 (worktree·.bak·debate log 추가)

### D2. 임계값 설정
- ① 현재 카운트 +/- 10% (현실 기반)
- ② 합의 명시 (B1 36/50/30 그대로)
- ③ 목표 기반 (예: hook 24, skill 30, memory 25 — 적극 감축)

### D3. 강제 메커니즘
- ① advisory: invariant 추가만 (B1 settings_drift처럼 WARN)
- ② commit_gate: 신규 hook/skill/memory 추가 시 기존 1개 제거 증명 강제 (차단)
- ③ 하이브리드: 신규 추가는 advisory(commit 통과), 임계 초과 시 commit_gate 차단

### D4. 제거 우선순위 산출
- ① 사용 빈도 (hook_log 마지막 호출 시각)
- ② 마지막 수정일 (mtime)
- ③ 명시적 deprecate 마커 (`_archive/`, `.deprecated` 등)

### D5. 위반 시 처리
- ① 차단만 (commit deny)
- ② 차단 + 자동 정리 후보 제안 (제거 우선순위 1순위 alert)
- ③ 차단 + 토론 강제 (B 분류 자동 승격)

## Claude 독립 의견 (먼저 제시)

D1: **②5개 전체** — 핵심 3개만으론 누락. 상위 5개 (hook/skill/memory/command/agent) 동시 도입. ③확장은 세션 부담.

D2: **②합의 명시 + 일부 조정** — B1 합의값 유지하되, 현재 카운트 기반 보정:
- hook 36 (현재 44 → 8개 감축 목표)
- skill 50 (여유 12 → 추가 가능 12)
- memory 30 (현재 38 → 8개 감축 목표)
- command 30 (현재 30 → 추가 시 제거 강제)
- agent 12 (현재 9 → 여유 3)

D3: **③하이브리드** — 일상 추가는 advisory(commit 통과 + WARN 누적)로 마찰 최소화. 임계 N% 초과(예: 130%) 시 commit_gate 차단. 단, 사용자 명시 override 1회 허용.

D4: **②마지막 수정일 + ① 사용 빈도 결합** — mtime 90일+ AND hook_log 미호출 = 1순위 후보. 현재 카운트만으로 결정 X.

D5: **②차단 + 정리 후보 제안** — 차단만은 사용자 좌절. 정리 후보 자동 제안하면 1초 클릭으로 해결.

추가 위험:
- 1세션 내 다수 변경 시 카운트 일시 폭증 → 디바운스 필요
- 제거 후보 자동 제안이 잘못되면 핵심 hook 삭제 위험 → 보호 리스트 필요

## 양측에 묻는 핵심 질문

1. D1~D5 각 결정 동의/이의/추가 안?
2. 임계값 D2 — 현재 카운트 기반 vs 적극 감축 목표?
3. hook 44→36 감축 = 8개 제거. 우선순위 산출 알고리즘?
4. commit_gate 차단이 사용자 좌절 유발 위험 — 면제 조건?
5. 보호 리스트 (절대 제거 금지 hook/skill) 명세 방법?

응답 형식: 각 결정·질문에 1~3문장. 한국어. 단순 동조 금지. B 분류이므로 깊은 비판 환영.
