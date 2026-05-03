# Round 2 — Claude 독자 답안 (선행 작성)

> Step 6-0 강제. 양측 본론 수령 전 작성. round_count=2 / max_rounds=3.
> 입력: round1 합의 (consensus.md) + R5_dry_run_report.md + 사용자 결정 (세트 A 안전 우선).
> 보류 쟁점 3건에 대한 본 라운드 본론.

## 결론 1줄

**4지표 목표선은 R5 분석 데이터로 모두 확정 가능. 메타 0 경계는 "셋팅 보완 가능 영역(파일·권한·검증)"과 "행동 교정(명제·인지)" 이분이 충분. GLOSSARY.json은 도메인 정리 가치 있음, RAG는 시기상조 (수동 grep로 충분).**

---

## 의제 R2-1. 헤비유저 4지표 목표선 구체 수치

R5 결과 + 사용자 세트 A 결정으로 모두 확정 가능:

| 지표 | 현재 | 합의 목표선 | 근거 |
|------|------|-----------|------|
| Always-loaded 토큰 | ~7,100 | **< 1,000** | 합의안 v2 명시 |
| rules/* 줄 수·파일 수 | 300줄·5개 | **100줄·1개** | citypaul v3 209줄 전례 |
| Slash command 수 | 33개 | **5개** | Shrivu Shankar magic command list 안티패턴 |
| Skill 평균 줄 | 305 | **80** | johnlindquist 70-82% 압축 실측 |
| Hook 파일 수 | 36 (settings 등록) / 45 (전체) | **5** | 사용자 세트 A 결정 |
| Subagent 수 | 9 | **5** | Anthropic 권장 + critic-reviewer + settlement·line·report·verify |
| Permissions | 130 | **15** | disler/hooks-mastery 12개 전례 |
| Worktree | 17 | **3** | Boris 10-15 / 사용자 단일 세션 운영 |

**라벨**: 실증됨 (R5 + 사용자 결정 + 헤비유저 실측 데이터 모두 일치)

---

## 의제 R2-2. "행동 교정 메타 0"의 경계

### 보존 카테고리 (= 안전·기능)
- 파일 접근 차단 (block_dangerous)
- 보호 파일 차단 (protect_files)
- commit 정합성 (commit_gate)
- 세션 진입 상태 로드 (session_start_restore)
- 완료 검증 (completion_gate)

### 폐기 카테고리 (= 행동 교정)
- "지침 읽으라" (instruction_read_gate, skill_instruction_gate)
- "plan 만들라" (r1r5_plan_check)
- "위험 평가하라" (risk_profile_prompt)
- "허가 정리하라" (permissions_sanity)
- "skill drift 감지하라" (skill_drift_check)
- "토론 진입 전 CLAUDE 읽으라" (navigate_gate)
- "하네스 분석 강제" (harness_gate)
- "evidence 마킹하라" (evidence_*)

### `incident_quote.md` 경계 판정
- **본문은 안전 가이드** (incident 데이터 인용 절차 = 사용자 결정 도움)
- **그러나 적용 트리거가 명제형** ("session_start hook 출력에 N건 보이면 응답 도입부 1블록 인용")
- 처리: **rules/*에서 폐기**. 도메인 incident 인용은 session_start_restore.sh가 자체 출력 (이미 incident_repair.py 호출). 별도 룰 불필요.

**라벨**: 실증됨 + 일부 환경미스매치 (incident_quote.md 위치)

---

## 의제 R2-3. GLOSSARY.json + RAG 도입 여부

### GLOSSARY.json — **채택**
- 한국어 제조업 용어(품번 / 라인 / 공정코드 / SUB ASSY / 메인서브 / OUTER / D0 / 잡셋업 등)가 도메인 SKILL.md 21개에 흩어져 있음 (각 SKILL.md 평균 305줄의 일부)
- 단일 `90_공통기준/GLOSSARY.json` 또는 `90_공통기준/glossary/` 디렉토리에 분리
- 효과: SKILL.md 평균 305줄 → 80줄 압축에 직접 기여 + 도메인 용어 단일 원본
- 부담: 단일 PR Phase 5 (Skill 압축)에 흡수. 추가 시스템 아님.

### RAG (Retrieval-Augmented Generation) — **시기상조 / 보류**
- Gemini 제안의 본질: SKILL.md에 박힌 용어를 RAG로 동적 호출
- 현재 환경: Claude Code 토큰 절약 + on-demand 로딩 = 이미 RAG 유사 효과
- 추가 시스템(vector DB·embedding 모델·검색 인터페이스) 도입은 메타 누적 부패 위험
- 처리: **수동 grep + Glob + Read로 충분**. RAG는 메타 0 안정화 후 별건 plan.

**라벨**: GLOSSARY 채택 (실증됨) + RAG 보류 (과잉설계 위험)

---

## 약점 예상

### 약점 1. "Skill 평균 305→80줄"은 GLOSSARY 분리만으로 달성 어려움
- 반박: johnlindquist 사례는 70-82% 압축. Skill에 박힌 (a) 용어 → GLOSSARY (b) 절차 상세 → MANUAL.md 분리 (c) 검증 명령 호출 → Python verify 치환. 3단 분해로 80줄 도달.
- 한계: line-batch-management 714줄은 워낙 커서 압축 후에도 200줄+ 가능. 도메인 특수성 인정.

### 약점 2. Permissions 130→15는 너무 급진적
- 반박: 130개 중 1회용 16건 + 중복 2건은 즉시 폐기. 나머지 112개를 포괄 패턴(`Bash(cmd:*)`)으로 통폐합하면 15-20개로 압축.
- 한계: 일부 1회용 permission이 실제 도메인에서 필요할 수 있음. Phase 6에서 telemetry 측정 후 조정.

### 약점 3. Worktree 17→3은 사용자 워크플로우 변경 강요
- 반박: R5 분석에서 worktree 17개는 대부분 비활성. 활성 worktree 분류 후 prune. 3개는 Boris 권장 최소.
- 한계: 사용자가 "활성"이라 분류하면 그 수 그대로. 절대 강요 아님.

### 약점 4. GLOSSARY 채택 후 유지보수 부담
- 반박: 한 번 만들면 도메인 용어 단일 원본. SKILL.md 변경 시 GLOSSARY 변경 발생 빈도 낮음 (제조업 용어는 안정적).

---

## 착수·완료·검증 조건

### 착수 조건 (Round 2 합의 후)
1. 4지표 목표선 모두 양측 동의
2. 메타 0 경계 (incident_quote.md 폐기 포함) 양측 동의
3. GLOSSARY 채택 + RAG 보류 양측 동의

### 완료 조건 (단일 PR + Phase 8단계)
1. 단일 PR (08afa889 + R5 + 세트 A 결정 반영) 작성·머지
2. Phase 1~9 (consensus.md 참조) 7일 측정 통과
3. 30일 후 4지표 모두 목표선 진입

### 검증 조건
1. always-loaded 토큰 1000 미만 측정 hook 1개 (token_threshold_check 활용)
2. PR 첫 커밋에 삭제 목표 수치 명시 + 이후 추가 시 PR 거부
3. R5_dry_run_report 통과 + 사용자 세트 A 결정으로 깨지는 동작 사용자 정의 안

---

## 다음 단계

1. GPT에 R5 통과 + 보류 쟁점 3건 본론 송부
2. Gemini에 동일 본론 송부
3. 양측 교차 검증
4. Claude 종합안 + 양측 검증
5. round_count=2 / pass_ratio ≥ 2/3 → 합의 종결 또는 Round 3
