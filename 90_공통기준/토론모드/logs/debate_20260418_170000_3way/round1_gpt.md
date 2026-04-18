# Round 1 — GPT 응답 (의제3 skill-creator 경로화)

## 요약
1. **래퍼 방식 찬성**. Claude Code 공식 자동 인식 경로는 `.claude/commands/*.md` + MCP `/mcp__서버명__프롬프트명`. `90_공통기준/스킬/<name>/SKILL.md`를 팀 원본, `.claude/commands/<name>.md`는 얇은 래퍼. 심볼릭 링크는 운영체제·권한 이슈, 단일 경로는 저장소 문서 체계 약화.

2. **우선순위는 호출빈도만으로 부족**. 기준: 변경 빈도 + 복잡도 + 참조 주체 수 + 인자 구조·실행 규칙 길이 → 호출빈도. 공식 커스텀 커맨드 frontmatter(description/argument-hint/allowed-tools/model) 붙일 수 있으니 길고 자주 바뀌고 인자 규칙 복잡한 명령일수록 저장소 스킬 원본. 1순위: debate-mode, settlement, line-batch-*, daily. 얇은 단발 지시문은 커맨드 경로 유지.

3. **동기화: Write hook보다 skill-creator 내부 자동 실행 맞음**. Write hook은 범위 너무 넓어 unrelated 수정에도 반응, 사람 손본 래퍼 덮어쓸 위험. skill-creator가 진입점이니 거기서 래퍼 생성, 예외만 수동 sync 명령 보정. `.claude/commands`가 공식 경로이므로 생성 시점 동기화로 drift 줄임.

4. **기존 중복 15개 3단계 분리**:
   - **지금 이관**: debate-mode, settlement, line-batch-*, daily (길고 자주 수정·규칙 많음)
   - **점진 이관**: doc-check, review-claude-md, self-audit, task-status-sync, map-scope (중간 복잡도)
   - **유지**: 얇은 단발 프롬프트, 개인 환경 의존·실험용 커맨드

5. **plugin:skill / SKILL.md 공식 정합성 약함**. 확인된 공식 Claude Code 구조:
   - `.claude/commands/*.md` 프로젝트 커맨드
   - `~/.claude/commands/*.md` 개인 커맨드
   - `.claude/agents/*.md` 서브에이전트
   - MCP `/mcp__서버명__프롬프트명`
   - `SKILL.md`/`plugin:skill`이 Claude Code 네이티브 자동 인식이라는 공식 설명은 찾지 못함
   → SKILL.md 체계는 저장소 내부 표준으로 유지, Claude Code 정합성은 `.claude/commands` 래퍼로.

## 한 줄 결론
래퍼 방식 + skill-creator 내부 동기화 + 3단계 이관 + 공식 정합성은 `.claude/commands/`로 확보.
