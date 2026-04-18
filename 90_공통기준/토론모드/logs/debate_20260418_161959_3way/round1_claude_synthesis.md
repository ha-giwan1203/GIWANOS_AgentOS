# Round 1 — Claude 종합 설계안 (의제1)

## 최종 매트릭스 설계

### Tier 1: 실행 모드 게이트 (GPT 제안, 양측 동의)
작업을 먼저 3개 실행 모드로 분류:
- **Cloud**: Anthropic 원격. fresh clone, `claude/` 브랜치만 push, 로컬 파일 접근 불가
- **Desktop**: Claude Code 앱 로컬 실행. 로컬 파일·도구 직접 접근 가능. 앱/PC 깨어 있어야 작동
- **/loop**: 세션 스코프 (영속성 없음, 현 세션 내만)

### Tier 2: Cloud 분류 4칸 (현 매트릭스 적용)
제목: **"원격 Cloud /schedule 분류표"**

| 축 | 판별 기준 | 주의 |
|----|----------|------|
| GitHub-only | Git·파일읽기·파이썬·쉘만. 네트워크 없음 | **+2차 검증**: 로컬 env·비밀키 의존성 없어야 함 (Gemini) |
| 커넥터 | Gmail/Notion/Slack/NotebookLM MCP | **Phase 2로 이월**: 토큰 주입 파이프라인 선결 |
| 로컬 실물 | xlsx/pptx 외부 경로 | Cloud 이관 불가 → Desktop 축으로 |
| 사내망 | G-ERP/Flow/MES + Chrome MCP | Cloud·Desktop 모두 불가 → 로컬 Desktop에서만 |

### Tier 3: Phase 1 Cloud 이관 후보 (보수, 양측 합의)
**3종 읽기 전용 한정**:
1. `/self-audit` — 시스템 자기진단 (읽기 전용)
2. `/doc-check` — 문서 정합성 검토 (읽기 전용)
3. `/review-claude-md` — CLAUDE.md 구조 검토 (읽기 전용)

**후보 제외 사유**:
- `/memory-audit` — MEMORY 수정·정리·커밋 가능성 있으면 제외. 읽기 모드만 별도 분리 시 재검토.
- `/task-status-sync` — Cloud는 `claude/` 브랜치만 push 허용 → main 직행 아키텍처와 상충
- `/map-scope` — 고위험 수정 전 선언 스킬로 원격 스케줄 부적합

### 하이브리드 작업 처리 (Gemini 우려 해소)
**하이브리드 5번째 축 신설 안 함**. Gemini 본인 교차 검증에서 GPT 게이트 방식 우위 인정.

**해결 구조**: 사내망 수집 단계와 분석/문서화 단계 분리
```
[로컬 Desktop] 사내망 수집 → Git commit → [Cloud] 분석·문서화·리포트
```
Cloud 측 분석 부분만 GitHub-only 축 편입. 수집은 로컬 Desktop 유지.

## Phase 별 로드맵

### Phase 1 (즉시 착수 가능)
- 3종 읽기 전용 Cloud 스케줄 등록
- 실행 주기: 주 1회 (월요일 오전 권장)
- 결과: `claude/audit-YYYYMMDD` 브랜치 PR로 수령

### Phase 2 (1주 운영 후)
- Phase 1 실패율 10% 미만이면 Phase 2 진입
- 커넥터 축 실증: NotebookLM MCP 원격 실행 가능 여부 POC
- 토큰 주입 파이프라인 설계

### Phase 3 (Cloud connector 실증 후)
- NotebookLM subagent 원격 편입
- Notion/Slack 자동 리포트 (별건)

## 근거 링크
- GPT Round 1: `round1_gpt.md`
- Gemini Round 1: `round1_gemini.md`
- 교차 검증: `round1_cross_verify.md`
