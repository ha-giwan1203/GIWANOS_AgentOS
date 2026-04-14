# /self-audit — 시스템 자기진단 메타 스킬

읽기 전용으로 에이전트 시스템 전체를 진단하고 리포트를 출력한다.
파일 수정 금지. 개선안 적용은 사용자 승인 후 별도 작업.

## 실행 절차

### Step 1 — 입력 수집 (읽기 전용)

아래 순서로 읽는다. settings.local.json이 1순위.

| 순서 | 대상 | 경로 | 확인 내용 |
|------|------|------|----------|
| 1 | 활성 hooks 등록 | `.claude/settings.local.json` | 등록된 hook 목록, 매처, 실행 순서 |
| 2 | hook 실파일 | `.claude/hooks/*.sh` | 등록 vs 실존 대조 |
| 3 | hooks README | `.claude/hooks/README.md` | 문서화 상태, fail-open/fail-closed 계약 |
| 4 | rules | `.claude/rules/*.md` | 규칙 체계 |
| 5 | commands | `.claude/commands/*.md` | 커맨드 목록 |
| 6 | agents | `.claude/agents/*.md` | 에이전트 목록 |
| 7 | 스킬 | `90_공통기준/스킬/*/SKILL.md` | 스킬 체계 |
| 8 | CLAUDE.md | 루트 + 도메인 하위 | 운영 지침 |
| 9 | 운영 흔적 | `incident_ledger.jsonl`, `hook_log.jsonl`, `skill_usage.jsonl` | 최근 7일 or 최근 50건만 |
| 10 | 상태 문서 | `TASKS.md`, `HANDOFF.md`, `STATUS.md` | 드리프트 여부 |

### Step 2 — 4축 진단 + 빈도 분석

`python3 .claude/hooks/incident_review.py --days 7 --threshold 3` 실행 결과를 진단에 포함.
임계치 초과 항목 존재 시 다음 세션 안건으로 추천.

| 축 | 설명 | 검사 내용 |
|----|------|----------|
| **활성등록 정합** | settings 등록 vs 실파일 존재 vs 문서 기재 | 등록됐는데 파일 없음 / 파일 있는데 미등록 / 문서 누락 |
| **문서 드리프트** | Git 실물 vs 문서 기술 불일치 | README/STATUS/HANDOFF가 실제 구조와 다른 곳 |
| **실패계약 위험** | hooks README 표 기준 fail-open/fail-closed 기재 여부 | README 표에 미기재 hook / 표 기재와 실제 동작 불일치 가능성 |
| **죽은 자산** | 참조되지 않는 파일/hook/rule | 어디서도 호출 안 되는 자산 식별 |

### Step 3 — 3분류

모든 진단 대상을 아래 3분류로 나눈다.

| 분류 | 정의 |
|------|------|
| **active** | 등록 + 실파일 존재 + 문서 기재 일치 |
| **archived** | `_archive`, `98_아카이브`, 비활성 명시 |
| **anomaly** | 위 둘에 해당하지 않는 불일치 (등록인데 파일 없음, 파일인데 미등록, 문서 누락 등) |

### Step 4 — 리포트 출력

```
## /self-audit 진단 결과

실행 시각: [KST]
Git 기준: [현재 HEAD SHA]
로컬 활성: settings.local.json [읽기 성공/실패]

### 요약
[1줄 종합 판정]

### P0~P3 리스크
| 등급 | 대상 | 문제 | 근거 파일 | 현재 상태 | 왜 문제인지 | 추천 수정 |
|------|------|------|----------|----------|-----------|----------|

### 항목별 진단
| # | 대상 | 분류 | 축 | 문제 | 영향 범위 | 되돌리기 난이도 |
|---|------|------|-----|------|----------|--------------|

### 인시던트 빈도 분석
[incident_review.py --days 7 --threshold 3 출력 결과]

### 다음 세션 안건 추천 (해당 시)
| 안건 | 근거 | 우선순위 |
|------|------|----------|

### 교차검증 권장
[GPT 토론모드로 검토 권장하는 항목]

### 제외/미확인
[archived 항목 + settings 읽기 실패 시 미확인 항목]
```

## 위임
진단 분석은 `self-audit-agent`에 위임한다.

```
Agent(subagent_type="self-audit-agent", prompt="위 Step 1~4 절차대로 진단 실행")
```

## 제약
- [NEVER] 파일 수정 금지 — Read/Grep/Glob/Bash(읽기 명령만) 허용
- [NEVER] 자동 적용 금지 — 리포트 출력 후 종료
- [SHOULD] GPT 토론모드 교차 검증 권장
- [SHOULD] 리포트를 TASKS.md 다음 안건에 반영 권장

## 출처
- 영상분석 c-a4GBOxhXQ "나의 AI 에이전트 전환기" A등급 적용
- GPT 토론 합의 (2026-04-12): 4축 진단, 3분류, settings 1순위
