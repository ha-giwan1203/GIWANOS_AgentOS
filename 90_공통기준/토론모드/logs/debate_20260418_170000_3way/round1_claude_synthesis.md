# Round 1 — Claude 종합 설계안 (의제3 skill-creator 경로화)

## 최종 구조

### 1. 경로 구조
```
원본 (팀 기준): 90_공통기준/스킬/<name>/SKILL.md
                 ↓ skill-creator 내부 자동 생성 (Gemini+GPT 동의)
래퍼 (Claude Code 공식 인식): .claude/commands/<name>.md
```

### 2. 래퍼 파일 템플릿
```markdown
---
description: [저장소 스킬에서 자동 복사]
argument-hint: [선택, 인자 있을 때]
allowed-tools: [선택]
---

# /{name}

저장소 스킬 원본: [90_공통기준/스킬/{name}/SKILL.md](../../90_공통기준/스킬/{name}/SKILL.md)

`Skill(skill="{name}")` 호출 또는 해당 SKILL.md 지침대로 실행.
```

공식 Claude Code frontmatter 규격 준수.

## 이관 로드맵 (타협안)

### Phase A — 즉시 이관 (세션69 내)
- **debate-mode** — 3자 토론 로직 복잡 + 최근 빈번 수정
- **settlement** — 7단계 정산 파이프라인
- **line-batch-*** (4종: management/outer-main/mainsub/validator) — ERP 도메인 의존 최대
- **daily** — 매일 반복, 다중 스킬 통합

**근거**: 변경빈도 + 복잡도 + 인자 구조 + 도메인 의존성 모두 높음. GPT 1순위 + Gemini "도메인 의존성" 기준.

### Phase B — 7일 내 점진 이관 (세션70~72)
- doc-check, review-claude-md, self-audit, task-status-sync, map-scope
- memory-audit (읽기 모드), auto-fix
- 중간 복잡도. Gemini의 "분열 현상 방지" 우려 해소 기한 설정.

### Phase C — 커맨드 경로 유지
- share-result, gpt-send, gemini-send, gpt-read, gemini-read (토론 기초)
- ask-gemini, debate-verify (유틸)
- 얇은 단발 프롬프트, 슬래시 호출 빈번, 구조 단순

## 자동 동기화 (이중 배치)
### 1차: skill-creator 내부 (생성/변경 시점)
- 신규 SKILL.md 작성 시 `.claude/commands/<name>.md` 래퍼 자동 생성
- 기존 SKILL.md 수정 시 래퍼의 description/frontmatter 갱신
- 사람이 래퍼를 직접 수정한 경우 덮어쓰지 않음 (hash 비교)

### 2차: 커밋 관문 (Gemini 지적 수용)
- pre-commit hook `skill_drift_check.sh` 신규
- `90_공통기준/스킬/*.skill` 변경 시 대응 `.claude/commands/<name>.md` 존재·정합성 검증
- 래퍼 수동 편집 drift 감지 시 경고 (커밋 차단은 Phase 2)

## 공식 정합성 (GPT 지적 수용)
- `SKILL.md` 체계는 **저장소 내부 표준**만 유지
- `plugin:skill` 자동 인식 주장은 **근거 부족** — 현 공식 문서 확인 범위 밖
- Claude Code 공식 자동 인식 경로만 신뢰:
  - `.claude/commands/*.md` 프로젝트 커맨드
  - `~/.claude/commands/*.md` 개인 커맨드
  - `.claude/agents/*.md` 서브에이전트
  - `/mcp__서버명__프롬프트명` MCP 프롬프트

## 우선순위 기준 (Gemini 제안 채택)
1. **도메인 의존성** (최우선) — 사내망/배치/정산 얽힌 스킬
2. **변경 빈도** (최근 3개월 커밋 수)
3. **복잡도** (SKILL.md + 리소스 파일 라인 수)
4. **인자 구조** (argument-hint 복잡도)
5. **참조 주체 수** (다른 스킬/hook에서 호출되는 횟수)
6. **호출 빈도** (마지막 가산점)

## 근거
- GPT Round 1: `round1_gpt.md`
- Gemini Round 1: `round1_gemini.md`
- 교차 검증: `round1_cross_verify.md`
