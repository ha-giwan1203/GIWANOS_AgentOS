# Round 1 — 교차 검증 (의제3)

## GPT → Gemini
**판정**: 이의
**근거**: 래퍼 방식·skill-creator 내부 자동+커밋 관문 검증 방향은 타당하지만, 중복 15개 지금 전부 즉시 이관은 위험. "공식 플러그인 규격과 정합" 주장도 공식 문서에서 확인되는 표준 경로는 `.claude/commands/` 프로젝트 커맨드뿐이라 과장.

## Gemini → GPT
**판정**: 이의
**근거**: 기존 중복 스킬을 점진 이관·유지로 남기면 문맥 인지 혼란(분열 현상) 근본 문제 방치, 15개 모두 즉시 저장소 스킬로 원본 통일 필요. 커밋 관문 무결성 검증 로직 누락 — 작업자 수동 편집 시 동기화 깨질 리스크.

## Claude 타협안
- **래퍼 방식** (양측 동의) → 채택
- **공식 정합** (GPT 지적) → SKILL.md는 저장소 내부 표준, Claude Code 정합성은 `.claude/commands/` 래퍼로 (GPT 견해 채택, Gemini "플러그인 규격 정합" 수정)
- **이관 시기** (대립) → **단계별 타협**:
  - **즉시 이관**: debate-mode, settlement, line-batch-* (4종), daily — 복잡도·규칙 긴 스킬부터 (GPT 1순위 + Gemini 일부 수용)
  - **7일 내 점진**: doc-check, review-claude-md, self-audit, task-status-sync, map-scope, memory-audit, auto-fix (중간 복잡도)
  - **유지**: 얇은 단발 프롬프트 (share-result, gpt-send, gemini-send 등) — 슬래시 호출 빈번 + 구조 단순
  - Gemini "분열 현상" 우려는 7일 내 이관 완료로 해소
- **우선순위 기준** (Gemini 제안 채택) → 도메인 의존성 추가: 기존 변경빈도/복잡도/참조 + **도메인 의존성(사내망/배치/정산)** 가산점
- **동기화 배치** (Gemini 이중 배치 채택) → skill-creator 내부 자동 생성 + 커밋 관문에서 drift 검증 (사람 손본 래퍼 덮어쓰지 않도록 hash 비교)
