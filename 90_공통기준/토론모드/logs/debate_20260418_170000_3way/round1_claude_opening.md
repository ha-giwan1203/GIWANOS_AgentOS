# Round 1 — Claude 독립 초안 (의제3 skill-creator 경로화 범위)

## 배경
- 세션68에서 "신규 스킬만 스킬 경로 우선, 기존 `.claude/commands/*.md` 점진 이관" 결정됨
- 이관 우선순위·기준·자동화 여부 구체화 안 됨

## 현 상태 (2026-04-18 기준)
- 저장소 스킬 경로(`90_공통기준/스킬/<name>/SKILL.md`): 19개 .skill 파일
- Claude Code 커맨드 경로(`.claude/commands/*.md`): 30개
- 중복: debate-mode, chomul-module-partno, daily, flow-chat-analysis, line-batch-*, production-report 등 약 15개 이상 양쪽에 공존

## 두 경로 차이

| 항목 | 저장소 스킬 (`90_공통기준/스킬/`) | Claude Code 커맨드 (`.claude/commands/`) |
|------|------------------------------|------------------------------------|
| 위치 | 저장소 내 업무 폴더 | `.claude/` 내부 |
| 트리거 | SKILL 메타데이터 (frontmatter) | 슬래시 커맨드 이름 |
| 호출 | `Skill(skill="name")` | `/name` |
| 구조 | `/<name>/SKILL.md` + 리소스 | 단일 `.md` 파일 |
| 메타 | name/description/version | 단순 지시문 |
| 장점 | 리소스·하위 파일 함께 관리 | 즉시 슬래시 호출 |
| 단점 | 호출 시 Skill tool 우회 | 큰 스킬은 파일 1개로 부족 |

## 쟁점
1. **두 경로 병존 유지 vs 단일화?**
2. **단일화 시 어느 쪽? 저장소 스킬 vs Claude Code 커맨드?**
3. **이관 우선순위 기준**: 호출 빈도 / 복잡도 / 리소스 파일 수 / 최근 수정일?
4. **자동 동기화 스크립트** vs **수동 이관**?
5. **Claude Code 공식 `/skill-creator` vs 저장소 `skill-creator-merged` 역할 분담**?
6. **이관 시 하위 호환**: 기존 `/debate-mode` 슬래시 호출 유지 필요한가?

## Claude 독립 판단
- **두 경로 병존 유지가 실용적** — Claude Code 슬래시 호출 UX(탭 자동완성)는 커맨드 경로만 가능. 저장소 스킬은 메타·리소스 관리 장점.
- **단방향 생성 원칙**: 저장소 스킬을 원본으로, `.claude/commands/*.md`는 **자동 생성된 슬래시 래퍼** (원본 참조 1~2줄)
- **자동 동기화 스크립트** 필요: 저장소 스킬 작성 시 `.claude/commands/<name>.md`를 자동 생성 (SKILL.md 경로 링크 + 지시문 요약)
- **이관 우선순위**:
  - 1순위: 자주 호출되는 대형 스킬 (debate-mode, settlement, line-batch-*)
  - 2순위: 리소스 파일 다수 포함 스킬
  - 3순위: 단순 지시문 스킬은 커맨드 경로 유지 가능
- **공식 `/skill-creator`는 신규 스킬 생성 시** 사용, 저장소 `skill-creator-merged`는 기존 스킬 구조 맞춤 작업 시

## 권고 구조 (Claude 초안)
```
원본: 90_공통기준/스킬/<name>/SKILL.md (실제 지시문·리소스)
        ↓ 자동 생성 스크립트
래퍼: .claude/commands/<name>.md (1~2줄 경로 참조)
```

### 래퍼 템플릿
```markdown
# /{name}

저장소 스킬: [90_공통기준/스킬/{name}/SKILL.md](../../90_공통기준/스킬/{name}/SKILL.md)

Skill(skill="{name}") 호출 또는 해당 SKILL.md 지침 따라 실행.
```

## 쟁점 요청 (양측)
1. 위 래퍼 방식이 합리적인가? 대안은?
2. 이관 우선순위 기준 (호출빈도/복잡도/리소스) 추가·수정?
3. 자동 동기화 스크립트 실행 지점: Write hook에서 자동? 또는 skill-creator 내부?
4. 기존 스킬 중 **지금 당장** 이관해야 할 것·유지할 것 구분?
