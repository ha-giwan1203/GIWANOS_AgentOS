# Plan: Subagent 확장 — settlement-validator + code-reviewer memory

> 출처: 영상분석 자동 모드 (2026-04-01)
> GPT 합의: A1→B 하향 + B1 범위 조정 (settlement-validator 우선, skills preloading 포함)
> 상태: **사용자 승인 대기**

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
description: 조립비 정산 파이프라인 검증 전용. 정산 결과 파일 대조, 합계 검증, 불일치 추적. 정산 관련 작업 후 자동 위임.
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

### 실행 순서
1. disallowedTools + memory 병용 테스트 (로컬)
2. 테스트 결과에 따라:
   - 병용 가능 → memory: project + disallowedTools: Write, Edit 적용
   - 병용 불가 → memory용 Write/Edit만 허용하되 system prompt에서 "memory 디렉토리 외 Write/Edit 금지" 명시
3. .gitignore 예외 여부 결정
4. frontmatter + system prompt 수정
5. GPT 검증 요청

---

## 3. doc-checker subagent (후순위)

현재 `/doc-check` 커맨드로 운영 중. subagent화 시 장점:
- 메인 컨텍스트 보호
- 더 깊은 교차 검증 가능

단, 기존 커맨드와 역할 중복 정리가 먼저.
settlement-validator 구현 완료 후 검토.

---

## 체크리스트

- [ ] settlement-validator.md 작성 + system prompt 완성
- [ ] assembly-cost-settlement 스킬 preloading 테스트
- [ ] code-reviewer disallowedTools + memory 병용 테스트
- [ ] 테스트 결과 기반 code-reviewer memory 적용 방안 확정
- [ ] GPT 검증 요청 (실물 기준)
