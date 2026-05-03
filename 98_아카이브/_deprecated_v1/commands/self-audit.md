# /self-audit — 시스템 자기진단 메타 스킬

읽기 전용으로 에이전트 시스템 전체를 진단하고 리포트를 출력한다.
파일 수정 금지. 개선안 적용은 사용자 승인 후 별도 작업.

## 실행 절차

### Step 1 — 입력 수집 (읽기 전용)

활성 hook 1순위 = `bash .claude/hooks/list_active_hooks.sh --full`. settings.json/local은 보조 (team hook 기준 + 개인 permissions 점검).

| 순서 | 대상 | 경로 / 명령 | 확인 내용 |
|------|------|------------|----------|
| 1 | 활성 hook 단일 원본(SSoT) | `bash .claude/hooks/list_active_hooks.sh --full` | 활성 hook의 SSoT (이벤트별 + 이름 리스트 + 총 고유 수). 세션93 합의 |
| 2 | team hook 등록 | `.claude/settings.json` | hooks 배열, 매처, 실행 순서, team permissions 기준 |
| 3 | 개인 permissions 점검 | `.claude/settings.local.json` | 1회용 패턴/중복 점검. **`hooks` 배열은 없는 게 정상** (현 운영 기준) |
| 4 | hook 실파일 | `.claude/hooks/*.sh` | SSoT vs 실존 대조 |
| 5 | hooks README | `.claude/hooks/README.md` | 문서화 상태, Failure Contract |
| 6 | rules | `.claude/rules/*.md` | 규칙 체계 |
| 7 | commands | `.claude/commands/*.md` | 커맨드 목록 |
| 8 | agents | `.claude/agents/*.md` | 에이전트 목록 |
| 9 | 스킬 | `90_공통기준/스킬/*/SKILL.md` | 스킬 체계 |
| 10 | CLAUDE.md | 루트 + 도메인 하위 | 운영 지침 |
| 11 | 운영 흔적 | `incident_ledger.jsonl`, `hook_log.jsonl`, `skill_usage.jsonl` | 최근 7일 or 최근 50건만 |
| 12 | 상태 문서 | `TASKS.md`, `HANDOFF.md`, `STATUS.md` | 드리프트 여부 |
| 13 | Git 상태 | `git rev-parse HEAD`, `git status --short`, `git diff --name-only`, `git diff --cached --name-only` | 미커밋 변경 시 "Git 기준 최종 판정 불가 / 로컬 임시검토" 표기 |

### Step 2 — 4축 진단 + 빈도 분석

`python3 .claude/hooks/incident_review.py --days 7 --threshold 3` 실행 결과를 진단에 포함.
임계치 초과 항목 존재 시 다음 세션 안건으로 추천.

| 축 | 설명 | 검사 내용 |
|----|------|----------|
| **활성등록 정합** | SSoT vs settings vs 실파일 vs README 4자 대조 | `list_active_hooks.sh --full|--names` 출력 ↔ `.claude/settings.json`(team) + `.claude/settings.local.json`(local) union ↔ hook 실파일 ↔ README 기재. 한 축이라도 어긋나면 anomaly |
| **문서 드리프트** | hooks README의 SSoT 문구와 실제 list_active_hooks 결과 대조 | README/STATUS/HANDOFF가 실제 구조와 다른 곳, 세션93 SSoT 합의 미반영 영역 |
| **실패계약 위험** | README Failure Contract와 active hook 전체 대조 | README 표 미기재 active hook / 표 기재와 실제 동작 불일치 가능성 |
| **죽은 자산** | commands/agents/skills/rules 참조 여부 | CLAUDE.md / AGENTS_GUIDE / commands / agents 어디서도 호출되지 않는 자산 식별 |

### Step 3 — 3분류

모든 진단 대상을 아래 3분류로 나눈다.

| 분류 | 정의 |
|------|------|
| **active** | `list_active_hooks.sh`에 표시 + 실파일 존재 + README/Failure Contract 문서화 일치 |
| **archived** | `_archive`, `98_아카이브`, 비활성 명시 |
| **anomaly** | 위 둘에 해당하지 않는 불일치 (SSoT엔 있는데 실파일 없음, 실파일 있는데 문서 없음, README엔 있는데 SSoT엔 없음, settings.local 단독 기준만으로 active 오판되는 항목 등) |

### Step 4 — 리포트 출력

```
## /self-audit 진단 결과

실행 시각: [KST]
Git HEAD: [현재 HEAD SHA]
Git status (--short): [요약 또는 "clean"]
unstaged: [git diff --name-only 결과 또는 "없음"]
staged: [git diff --cached --name-only 결과 또는 "없음"]
미커밋 변경 시 → "Git 기준 최종 판정 불가 / 로컬 임시검토" 표기

활성 hook 기준: list_active_hooks.sh --full [읽기 성공/실패, 총 N건]
settings.json: [읽기 성공/실패]
settings.local.json: [읽기 성공/실패, hooks 배열 부재 정상]

### 요약
[1줄 종합 판정]

### P0~P3 리스크
| 등급 | 대상 | 문제 | 근거 파일 | 현재 상태 | 왜 문제인지 | 추천 수정 |
|------|------|------|----------|----------|-----------|----------|

### 수정 후보 영향반경
- 대상:
- 직접 영향:
- 간접 영향:
- 회귀 위험:
- 권장 처리: [문서 보정만 가능 / C 모드 필요 / GPT 교차검증 필요 / 보류]

### 항목별 진단
| # | 대상 | 분류 | 축 | 문제 | 영향 범위 | 되돌리기 난이도 |
|---|------|------|-----|------|----------|--------------|

### 인시던트 빈도 분석
[incident_review.py --days 7 --threshold 3 출력 결과]

### 다음 세션 안건 추천 (해당 시)
| 안건 | 근거 | 우선순위 |
|------|------|----------|

### 교차검증 권장
[GPT 정밀평가 또는 토론모드 검토 권장 항목]

### 제외/미확인
[archived 항목 + SSoT/settings 읽기 실패 시 미확인 항목]
```

## 위임
진단 분석은 `self-audit-agent`에 위임한다.

```
Agent(subagent_type="self-audit-agent", prompt="위 Step 1~4 절차대로 진단 실행")
```

## C 모드 전환 조건

/self-audit 결과가 다음 경로 수정을 요구하면 **자동 적용 금지**. C 모드(plan-first + R1~R5)로 분리한다.

- `.claude/hooks/`
- `.claude/settings*.json`
- `.claude/commands/`
- `.claude/agents/`
- `90_공통기준/스킬/*/SKILL.md`
- `CLAUDE.md` (루트/도메인)
- `.claude/rules/*.md`

위 경로 수정은 시스템 수정 C 모드 대상이다. /self-audit는 수정하지 않고 리포트만 출력한다. 실제 수정은 plan-first + R1~R5 사용자 승인 후 별도 진행한다.

## GPT 정밀평가 역할 분리

/self-audit는 Claude 내부 1차 감사다. P0/P1 리스크 또는 hook/settings/command/agent 변경 필요가 산출되면 GPT 정밀평가(`90_공통기준/업무관리/gpt-skills/claude-code-analysis.md`) 또는 토론모드 교차검증을 권장한다 (SHOULD).

## 제약
- [NEVER] 파일 수정 금지 — Read/Grep/Glob/Bash(읽기 명령만) 허용
- [NEVER] 자동 적용 금지 — 리포트 출력 후 종료
- [NEVER] 진단 결과 기반 hook/settings/command/agent 즉시 수정 금지 (C 모드 전환 조건 참조)
- [SHOULD] GPT 정밀평가 또는 토론모드 교차 검증 권장
- [SHOULD] 리포트를 TASKS.md 다음 안건에 반영 권장

## 출처
- 영상분석 c-a4GBOxhXQ "나의 AI 에이전트 전환기" A등급 적용
- GPT 토론 합의 (2026-04-12): 4축 진단, 3분류
- 세션93 SSoT 합의 (2026-04-22): list_active_hooks.sh 단일 기준
- 세션134 (2026-05-01): C 모드 분리 + Git 상태 + GPT 정밀평가 권장 보강
