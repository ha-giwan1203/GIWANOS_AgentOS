# Plan: Subagent 확장 — settlement-validator + code-reviewer memory

> 출처: 영상분석 자동 모드 (2026-04-01)
> GPT 합의: A1→B 하향 + B1 범위 조정 (settlement-validator 우선, skills preloading 포함)
> 상태: **구현 완료** (2026-04-02 사용자 승인 → 즉시 구현)

---

## 1. settlement-validator subagent 신규 생성

### 목적
조립비 정산 파이프라인(Step 1~7) 실행 후 결과 검증을 전담하는 read-only subagent.
현재 수동 검증 → subagent 위임으로 메인 컨텍스트 보호.

### 파일 위치
`.claude/agents/settlement-validator.md`

### 설계안

```yaml
---
name: settlement-validator
description: 조립비 정산 파이프라인(Step 1~7) 검증 전용. 05_생산실적/조립비정산/ 하위 결과 파일 대조, 합계 검증, 불일치 추적. run_settlement_pipeline.py 실행 완료 후 또는 /settlement-validate 호출 시 위임.
model: haiku
tools:
  - Read
  - Grep
  - Glob
  - Bash
skills:
  - assembly-cost-settlement
---
```

### system prompt 핵심
- 정산 파이프라인 Step별 출력 파일 검증
- 기준정보 엑셀 vs 정산 결과 대조
- 합계 일치 검증 (내부 합계 + 원본 대비)
- 불일치 시 라인별/품번별 원인 추적
- PASS/FAIL/WARNING 판정 출력

### tool 제한 근거
- Read/Grep/Glob: 파일 읽기 + 검색
- Bash: python 스크립트 실행(검증용), git diff
- Edit/Write 제외: 검증 전용, 수정 금지

### 위임 조건 (과발동 방지)
- 트리거 1: run_settlement_pipeline.py 실행 완료 후 (메인 agent가 명시적 위임)
- 트리거 2: 사용자 명시 호출 `/settlement-validate`
- 금지: "정산" 키워드 매칭 기반 자동 트리거 (오탐 위험)
- 금지: 파일 열람만으로 트리거 (파이프라인 실행 없는 조회는 대상 아님)
- 중복 방지: 같은 파이프라인 실행에서 1회만 위임 (완료 마커 또는 최종 산출물 기준)
- description에 경로(05_생산실적/조립비정산/)와 트리거 조건 명시 → context 기반 위임 정확도 확보

### skills preloading
- `assembly-cost-settlement` 스킬 주입 → 정산 도메인 지식 자동 로드
- 기존 도메인 CLAUDE.md 규칙 자동 적용

---

## 2. code-reviewer memory 추가 (A1 → B등급)

### 문제점 (GPT 지적, 실증 확인)
- `memory: project` 추가 시 **Read, Write, Edit 자동 활성화** (공식 문서 확인)
- 현재 code-reviewer는 tools: Read, Grep, Glob, Bash로 의도적 제한
- memory가 Write/Edit을 열면 "read-only reviewer" 성격 약화

### 확인 필요 항목
1. memory 활성화 시 Write/Edit 범위가 agent-memory 디렉토리에만 국한되는지?
   - 공식 문서: "Read, Write, and Edit tools are automatically enabled so the subagent can manage its memory files"
   - → memory 파일 관리 목적이나, 도구 자체는 전체 파일시스템 접근 가능
2. `disallowedTools: Write, Edit` + `memory: project` 병용 시 memory 작동 여부?
   - 공식 문서: "If both are set, disallowedTools is applied first, then tools is resolved"
   - → disallowedTools가 우선이면 memory가 동작 못할 수 있음. **테스트 필요**
3. .claude/agent-memory/code-reviewer/ Git 포함 여부
   - .claude/ 전체가 .gitignore → memory도 Git 미추적
   - 팀 공유 필요하면 별도 경로 설정 or .gitignore 예외 추가
4. MEMORY.md 비대화 방지 규칙
   - 200줄 제한 (공식 문서 기본값과 동일)
   - system prompt에 "MEMORY.md 200줄 이내 유지" 명시

### 테스트 케이스 (행동 증거 기반 판정)

| Case | 설정 | 성공 조건 | 실패 조건 |
|------|------|----------|----------|
| A | `memory: project` + `tools: [Read, Grep, Glob, Bash]` (Write/Edit 미포함) | memory 파일 생성됨 + 재세션 재사용 확인 | memory 파일 미생성 or subagent 동작 불가 |
| B | `disallowedTools: [Write, Edit]` + `memory: project` | memory 쓰기 차단됨 + subagent 정상 동작 유지 | Write/Edit 차단 안 됨 (disallowedTools 무력화) |
| C | `memory: project` + Write/Edit 허용 + PreToolUse hook guard | memory 파일 생성/재사용 + memory 경로 밖 Write/Edit 시도 시 hook이 차단 | hook 우회 or prompt 무시로 임의 파일 수정 |

판정 흐름:
1. Case A 테스트 → memory 쓰기 성공이면 A 채택 (최선: 도구 제한만으로 해결)
2. Case A 실패 → Case B 테스트 → 쓰기 차단 + 정상 동작이면 B 채택 (memory 포기, read-only 유지)
3. Case B에서 disallowedTools 무력화 확인 → Case C 테스트
4. Case C: PreToolUse hook로 `.claude/agent-memory/code-reviewer/` 밖 경로 Write/Edit 차단 (deterministic guard)

> Case C의 hook guard는 prompt-only 제한보다 안전. 이 프로젝트에서 이미 protect_files.sh, pre_write_guard.sh 패턴 운영 중이므로 동일 구조 활용.

### .gitignore 결정
- .claude/ 전체 .gitignore 현행 유지 (agent-memory 포함)
- 1인 개발 + AI 체제, 팀 공유 불필요
- 머신 교체 시 memory 유실 → code-reviewer memory는 프로젝트 구조 캐시 수준이라 자동 재학습 가능

### 테스트 결과 (2026-04-02 실행)

**Case A 실행**: memory: project + tools: [Read, Grep, Glob, Bash]
- 결과: Write/Edit 자동 활성화 **안 됨**. subagent에 Write/Edit 도구 미노출.
- memory 저장 불가. subagent 정상 동작은 유지.
- 판정: **memory 쓰기 불가 → memory 포기, read-only 현행 유지**

Case B/C 테스트 불필요 — Case A 결과로 결론:
- memory: project를 넣어도 tools 목록에 Write/Edit 없으면 자동 활성화 안 함
- code-reviewer는 현행 그대로 유지 (memory 없이 read-only)

### 최종 결정
- code-reviewer: 변경 없음 (memory 미적용, read-only 유지)
- settlement-validator: 신규 생성 완료 (.claude/agents/settlement-validator.md)

---

## 3. doc-checker subagent (후순위)

현재 `/doc-check` 커맨드로 운영 중. subagent화 시 장점:
- 메인 컨텍스트 보호
- 더 깊은 교차 검증 가능

단, 기존 커맨드와 역할 중복 정리가 먼저.
settlement-validator 구현 완료 후 검토.

---

## 체크리스트

- [x] settlement-validator.md 작성 + system prompt 완성 (2026-04-02)
- [ ] assembly-cost-settlement 스킬 preloading 테스트 (정산 데이터 입수 후)
- [x] code-reviewer memory 테스트: Case A 실행 → Write/Edit 미활성화 → memory 포기 결정 (2026-04-02)
- [x] 테스트 결과 기반 code-reviewer memory 적용 방안 확정: 현행 유지 (2026-04-02)
- [ ] GPT 검증 요청 (실물 기준) — 진행 중
