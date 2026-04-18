# Round 1 — Claude 독립 초안

> GPT/Gemini 의견 받기 전 Claude 단독 판단. 후속 라운드의 하네스 기준점.

## 1. 4칸 매트릭스 정의 (Claude 초안)

| 축 | 판별 기준 | 원격 실행 가능성 |
|----|----------|------------------|
| **GitHub-only** | Git·파일읽기·grep·파이썬·쉘만 사용. 네트워크 호출 없음 | ✅ `/schedule` 바로 이관 가능 |
| **커넥터** | Gmail/Notion/Slack/NotebookLM MCP 호출 포함 | ⚠️ MCP 접근 권한/토큰 원격 주입 가능 시 가능 |
| **로컬** | xlsx/pptx 등 로컬 파일시스템 실물 수정. 저장소에 커밋되지 않는 원본 경로 의존 | ❌ 원본이 로컬에 있으므로 원격 불가 |
| **사내망** | G-ERP/Flow/MES 브라우저 조작, Chrome MCP 필수 | ❌ 사내망+브라우저 의존 |

## 2. 현 스킬 37개 분류 (Claude 초안)

### GitHub-only (Phase 1 이관 1순위 후보)
- `/self-audit` — 읽기 전용 시스템 진단
- `/memory-audit` — MEMORY.md 비대화/중복 점검
- `/doc-check` — 문서 정합성
- `/review-claude-md` — CLAUDE.md 구조 검토
- `/task-status-sync` — TASKS↔STATUS↔HANDOFF 정합
- `/map-scope` — 영향 반경 선언 (읽기)

### 커넥터 (Phase 2 — 권한 주입 검증 후)
- Gmail: 없음 (현재 스킬)
- Notion: `/task-status-sync` 일부 (보조)
- Slack: 없음
- NotebookLM: `settlement-domain-expert`, `line-batch-domain-expert` subagent

### 로컬 (이관 불가 — 로컬 유지)
- `assembly-cost-settlement` — `05_생산실적` xlsx 실물
- `production-report` — 생산실적 엑셀
- `pptx-generator` — PPT 실물
- `daily-routine` — 일일 로컬 파일 생성
- `chomul-module-partno` — 초물표 xlsx
- `sp3-production-plan` — SP3 계획 xlsx

### 사내망 (이관 불가 — 사내망 유지)
- `line-batch-*` (4종) — G-ERP 라인배치
- `flow-chat-analysis` — 사내 Flow 채팅
- `night-scan-compare` — 사내 MES 스캔
- `production-result-upload` — MES 업로드
- `zdm-daily-inspection` — ZDM 시스템

## 3. Phase 1 이관 후보 (Claude 권고)

1. `/self-audit` — 스케줄 실행해 결과 PR/issue로 받기 좋음
2. `/memory-audit` — 주 1회 MEMORY.md 점검 자동화
3. `/doc-check` — 주 1회 문서 링크/참조 검증

## 4. 쟁점 (양측에 물어볼 것)
- **쟁점 A**: 로컬 파일 의존이지만 xlsx가 Git에 커밋되는 경우(예: TASKS.md 기반 집계) — GitHub-only 축으로 승격 가능한가?
- **쟁점 B**: NotebookLM MCP는 인증 토큰·브라우저 세션 필수 → "커넥터" 분류 자체가 원격 실행 가능한가?
- **쟁점 C**: `/schedule` 실행 환경의 정확한 제약(네트워크·MCP·파일 쓰기 범위) — 공식 문서 근거 필요
- **쟁점 D**: 이관 Phase 1 후보 3건이 적절한가, 추가/대체가 필요한가?

## 5. 독립 판단 (사전 명시)
- **로컬/사내망 분리는 필수** — GPT/Gemini가 통합 제안해도 반대
- **커넥터 축은 "조건부" 승격** — 실제 원격 MCP 호출 증명 없이 Phase 1 포함 반대
- **Phase 1은 3건 이하로 제한** — 범위 확장 제안 들어오면 보류 처리
