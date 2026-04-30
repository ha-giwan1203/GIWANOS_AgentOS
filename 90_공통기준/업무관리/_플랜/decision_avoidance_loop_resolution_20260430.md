# Claude 결정 회피 사고 패턴 — Self-Reinforcing Loop 해소 plan (세션132)

## Context

세션132 3자 토론 + Claude/GPT/Gemini 외부 자료 검색 결과 통합. 사용자 지적: Auto Mode 활성 상태에서 routine 운영 진행 중 Claude가 옵션 4지선다·(A)/(B) 의도 확인 떠넘김 5회 발화. H10·H11 강한 채택 (hook 회로 누적 + 구조적 사용자 의존 강제 규칙 누적).

3자 + 외부 자료 합의 4건 도출. 사용자 명시 "확인해서 진행" 지시(2026-04-30) → 위험도 분류 후 즉시/보류 분리 처리.

## 처리 결과

### 즉시 적용 완료 (2건)

| 항목 | 변경 | 위험도 |
|---|---|---|
| **Routine/시스템 분리 — work_mode_protocol.md 모드 A에 1줄 추가** | "routine 운영 즉시 실행 원칙" — D0/MES/정산/잡셋업/라인배치는 SKILL.md 규칙대로 즉시 실행, 옵션 4지선다·의도 확인 금지 | 낮음 (텍스트 추가, 가역) |
| **Graduated Trust — 토론모드 CLAUDE.md L100 예외 1줄 추가** | "routine 운영(A 모드)의 결정 영역은 B 자동 승격 적용 안 함" + 외부 ERP/MES 비가역·hook/settings·새 룰 추가는 본 예외 제외 | 낮음 (텍스트 추가, 가역) |

### 보류 — 사용자 결정 후 진행 (2건)

#### 보류 1: Context Slimming (hook 상태 → 별도 감사 로그 분리)

- **외부 자료 강한 보강**: Claude Code Hook 과밀 부작용 직접 보고 (PreToolUse 가짜 error 시그널 컨텍스트 200~400라인 누적 → Claude turn 조기 종료). 본 세션 H10 정확 일치.
- **위험도**: 매우 높음. `.claude/hooks/` 시스템 자체 수정 = 운영 자동화(D0/MES/잡셋업/정산/라인배치) 직접 영향. 잘못 만지면 매일 운영 깨질 가능.
- **선결 조건**:
  1. PreToolUse 18개 + Stop 5개 hook 중 어느 것이 가짜 error 시그널 발생시키는지 식별 (실측 필요)
  2. hook 출력을 모델 컨텍스트에서 제외하는 변경이 Claude Code 자체 설정에서 가능한지 확인 (`.claude/settings.json` hook output 처리 옵션)
  3. 분리 후 운영 자동화 회귀 테스트 (D0 morning/evening 1회씩 실증)
- **예상 작업량**: 모드 C plan 별건 + R1~R5 반증 + 1주 측정

#### 보류 2: Lineage-based 자동 검증 (Git 원본 대조 + 모순 시 자동 롤백)

- **Gemini 신규 제안 + 외부 자료 보강**: 신뢰 위임 프로토콜의 Consensus Corruption 위험을 Git 원본 lineage 대조로 보정.
- **위험도**: 중간. 신규 시스템 추가 = 기존 자동화에 영향 0이지만 새 코드 미실측.
- **선결 조건**:
  1. "Git 원본 대조" 대상 식별 (TASKS.md / SKILL.md / rules / settings 중 어느 것이 lineage 기준인가)
  2. 모순 자동 감지 로직 (incident_repair.py 확장 vs 신규 hook)
  3. 자동 롤백 vs 알람만 (자동 롤백은 비가역 행동이라 신중)
- **예상 작업량**: 모드 C plan 별건 + 신규 코드 100~200줄 + 실증

## 합의 매트릭스 (참고용)

| 의제 | Claude | GPT | Gemini | 외부 자료 | 처리 |
|---|---|---|---|---|---|
| Routine/시스템 분리 | 채택 | 채택 (B) | 반대→조건부 채택 | smart manufacturing HITL + guided autonomy | **즉시 적용** ✅ |
| 신뢰 위임 (2자 자동) | 보류 | 부분 채택 (routine만) | 자기 비판 후 보강 | Multi-agent debate 효과 + Consensus Corruption 위험 | **routine 한정 — 즉시 적용에 포함** |
| Graduated Trust 3계층 | 신규 채택 | 신규 채택 | 신규 채택 | guided autonomy 보강 | **즉시 적용** ✅ |
| Context Slimming | 신규 (H8 보강) | 신규 (control-plane) | 신규 (감사 로그) | Claude Code Hook 부작용 직접 보고 | **보류** (위험도 매우 높음) |
| Lineage-based 자동 검증 | 신규 보강 | 미언급 | 신규 제안 | (Gemini 외부 자료) | **보류** (실측 필요) |

## R1~R5 (즉시 적용 2건 한정)

- **R1 (진짜 원인)**: 본 세션 5회 떠넘김의 직접 트리거 = 토론모드 CLAUDE.md L81 "B 분류 감지 → 사용자 명시 호출 대기"가 routine 운영에도 적용된 결과. 본 변경은 routine A 모드의 결정 영역에 그 룰 적용 제외. 진짜 원인.
- **R2 (직접 영향)**: 텍스트 변경 2줄 (`work_mode_protocol.md` + `토론모드 CLAUDE.md`). hook/settings 영향 0. ERP/MES 영향 0.
- **R3 (간접 영향·grep)**: routine 키워드(D0/MES/정산/잡셋업/라인배치)는 이미 도메인 진입 표에 정의됨. 충돌 없음. 적용 범위 명시: 외부 ERP/MES 비가역 반영 + hook/settings 변경 + 새 룰 추가는 예외 제외.
- **R4 (선례)**: 세션131 incident_quote.md 신설 (2자 합의 + 사용자 명시 채택)과 동일 패턴. 안전.
- **R5 (롤백)**: git revert. 가역. ERP/MES/SmartMES 잔존 데이터 0.

## 검증

- 다음 routine 업무(D0 morning 또는 다른 정형) 진입 시 옵션 4지선다 재발 여부 = H1 검증
- 검증 신호 부정적이면 본 plan 보류 항목(Context Slimming) 우선순위 격상

## 참고 — 외부 자료 출처

- HITL cognitive load (MDPI)
- Smart Manufacturing HITL (MDPI)
- IBM Agentic AI Governance Playbook
- Claude Code Hook 과밀 부작용 외부 보고 (Gemini 검색)
- Multi-agent Debate (ICML 2024)
- Autonomy Paradox (Fortra)
- HITL escalation rate calibration (Strata.io)
