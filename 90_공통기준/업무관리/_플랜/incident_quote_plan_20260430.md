# [모드 C] 실패 대응 자동 진단 인용 개선 — plan

> 본 plan은 직전 [모드 B] 분석 plan을 대체. 분석 결과 + 3자 토론 합의 결과를 받아 C 모드 작업 plan으로 전환.
> v2 갱신 (2026-04-30): 사용자 조건부 승인 1차 피드백 반영 — jq 필터 OR 단일 select·null 방어·unresolved 명시 보강 + plan 위치 확정(`90_공통기준/업무관리/_플랜/`).

## Context

3자 토론 합의(Claude+GPT+Gemini, 본 세션):
- **자동 수리가 아니라 자동 진단 인용이 진짜 빈칸** — incident_ledger·hook_timing·classification_reason·next_action 전부 적재되지만, Claude가 응답 시 자동 인용하는 경로가 없음. session_start_restore.sh가 "12건 + /auto-fix 가능" 한 줄만 출력하고 끝남.
- **채택 범위 (2/3)**: 안1(`.claude/rules/incident_quote.md` 신설) + 안3(finish/daily/d0-plan 진입 점검 도메인 필터)
- **보류 (2/3)**: 안2(`/auto-fix` Step 0 자동 트리거) — auto-fix Step 1이 `smoke_test.sh + e2e_test.sh` 자동 실행 포함이라 트리거 발화 시 매 세션 무거운 회전 발생. 안1+3 적용 후 incident 감소 추이 보고 별건 결정.

목표: "자동으로 고치게" 하지 않는다. **"자동으로 보고 판단하게"** 한다.

---

## 변경 대상 파일 (4개 신설/수정 + 인덱스 1줄)

| 파일 | 변경 유형 | 줄 수 |
|------|----------|------|
| `.claude/rules/incident_quote.md` | **신규** | ~40줄 |
| `CLAUDE.md` (루트) | 인덱스 표 1줄 추가 | +1줄 |
| `.claude/commands/finish.md` | 진입 점검 1블록 추가 | +5~8줄 |
| `.claude/commands/daily.md` | 진입 점검 1블록 추가 | +5~8줄 |
| `.claude/commands/d0-plan.md` | 진입 점검 1블록 추가 | +5~8줄 |

**금지 (변경 없음 확인 대상)**:
- `.claude/hooks/*` 전체
- `.claude/settings*.json` 전체
- `commit_gate.sh`, `auto_commit_state.sh`, `evidence_gate.sh`, `completion_gate.sh`
- `incident_repair.py` 코드 (CLI는 기존 `--json --limit` 그대로 사용)

---

## R1~R5 반증 (질문형)

### R1 — 진짜 원인인가? 수정 없이 해결 가능한가?
- **진짜 원인**: incident 데이터 적재 정상. session_start 출력 정상. 누락은 **"Claude가 응답 진입 시 자동 인용해야 한다"는 운용 규칙 부재**.
- **수정 없이 해결 가능?**: 사용자가 매 세션 수동 요청하면 가능. 그러나 반복 4~5회/세션 발생 (실측: 미해결 12건이 하루 이상 누적되는데 매번 새로 묻는 패턴). 운용 규칙으로 표준화 필요.
- **결론**: 수정 = 규칙 문서 신설 + command 진입 1블록.

### R2 — 직접 영향
- **hook 동작 변화**: 없음. 새 hook 0개, 기존 hook 수정 0개.
- **skill 동작 변화**: 없음. auto-fix SKILL.md 변경 안 함 (안2 보류).
- **command 동작 변화**: finish / daily / d0-plan 3개. 진입 시 advisory 1회 추가. 차단 없음.
- **외부 ERP/MES 영향**: 없음. ERP/MES/SmartMES/Z드라이브 호출 0.
- **Claude 응답 동작**: 첫 턴에 미해결 incident ≥1건 시 incident_repair.py 출력 3줄 인용 후 본문 시작. 토큰 비용 ~30~80.

### R3 — 간접 영향 (grep, 공유 자원)
- **rules/ 신규 패턴**: 기존 5개 파일과 동형. 충돌 없음.
- **command 진입 점검 패턴**: 기존 finish.md Phase 1, daily.md Phase 0, d0-plan.md "첨부 파일 가드" 모두 advisory 진입 점검 사례 존재. 충돌 없음.
- **incident_ledger.jsonl**: 읽기 전용. 쓰기 없음.
- **incident_repair.py**: CLI 호출만, 코드 수정 없음.
- **CLAUDE.md 토큰**: 인덱스 1줄 +100바이트. 영향 무시 가능.

### R4 — 선례 검색
- **같은 선례**: `debate_20260428_201108_3way 빼는 안 1` (세션122) — 루트 CLAUDE.md에서 `.claude/rules/*.md` 5개 분리. 본 작업은 그 패턴의 일관 확장 (rules 1개 추가).
- **incident_ledger 동일 분류**: `evidence_missing` 9회·`pre_commit_check` 다수·`completion_before_state_sync` 2건 unresolved. 본 plan은 참조만, 수정 안 함.
- **D0 계열(세션107/110/115)과의 차이**: 세션107~115는 ERP/MES 외부 잔존·OAuth 흐름 변경. 본 작업은 외부 호출 0개·문서 변경만. 카테고리 다름.

### R5 — 롤백·잔존 데이터
- **비가역 행동**: 없음. 신규 파일 + 마크다운 추가만.
- **롤백 절차**:
  1. `git revert <commit-sha>` (단일 커밋)
  2. 또는 수동: `rm .claude/rules/incident_quote.md` + CLAUDE.md 1줄 제거 + commands 3개 추가 블록 제거
  3. `bash .claude/hooks/final_check.sh --fast` PASS 확인
- **잔존 데이터**: ERP/MES/SmartMES/Z드라이브 0. `.claude/incident_ledger.jsonl` 수정 없음 (읽기 전용 참조).

---

## 산출물 초안 1 — `.claude/rules/incident_quote.md`

```markdown
# 미해결 incident 자동 인용 규칙

> 합의 원본: 본 세션 3자 토론 (Claude·GPT·Gemini). 채택: 안1+안3. 보류: 안2.
> 배경: incident 데이터(`.claude/incident_ledger.jsonl`)는 정상 적재되지만, Claude가 응답 진입 시 자동 인용 경로가 없어 사용자가 매번 수동 요청하던 문제 해소.

## 트리거 조건

session_start hook 출력에 `--- 미해결 incident: N건` 라인이 보이고 N ≥ 1.

## 적용 절차

1. **첫 응답 본문 진입 전** 1회 실행:
   ```bash
   python .claude/hooks/incident_repair.py --json --limit 3
   ```
2. 출력에서 다음 3개 항목을 응답 도입부 1블록(3줄 이내)으로 인용:
   - 가장 최근/반복 fingerprint 기준 1건의 **classification_reason**
   - **inferred_next_action** (incident_repair.py가 제시하는 다음 행동)
   - **재시도 가능성** 한 줄 (advisory)
3. 인용 후 사용자 요청 본문 진행.

## 적용 예시 (GPT 1번 보강안)

### D0 실패 시
```
D0 실패 관련 최근 incident 3건 확인됨.
1) OAuth 콜백 정체 2회 반복 — RETRY_OK 가능
2) recover 로그 cp949 출력 오류는 1812603c에서 패치됨
3) 오늘 morning 로그 미확인 — 자동 재실행 전 중복 반영 여부 확인 필요

판단: 바로 재업로드 금지. 먼저 morning 로그와 SmartMES 반영 여부 확인.
```

### commit 실패 시
```
commit 관련 최근 incident 확인됨.
1) auto_commit_state가 수동 커밋 메시지를 선점한 이력 있음
2) commit_gate 차단 후 staged 풀림 신규 이슈 있음
3) final_check 실패 시 TASKS/HANDOFF/STATUS 동기화 필요

판단: 바로 commit 재시도 금지. staged 상태와 final_check 결과부터 확인.
```

## 적용 범위

- **적용**: 모드 A·C·E 첫 응답.
- **건너뜀**: 모드 B·D 첫 응답 (메타 응답).
- **세션 중 후속 응답**: 미적용.

## 금지

- incident 자동 resolve 호출 금지 (`--auto-resolve` 사용 금지).
- TASKS/HANDOFF 자동 등록 금지.
- 자동 수정·자동 hook 추가 금지.
- 사용자 결정 없이 incident 관련 파일 수정 금지.

## 비용

- 토큰 ~30~80 (3줄 인용).
- 실행 시간 ~수백 ms.
- 외부 호출 0.
```

---

## 산출물 초안 2 — 루트 CLAUDE.md 인덱스 추가

19라인(`공동작업 원칙`) 다음 줄 추가:

```markdown
| 미해결 incident 자동 인용 규칙 | [.claude/rules/incident_quote.md](.claude/rules/incident_quote.md) |
```

---

## 산출물 초안 3 — finish / daily / d0-plan 진입 점검 블록

> **jq 문법 보강 사유 (사용자 조건부 승인 1차 피드백 반영)**:
> - `(.hook // "")` null 방어 — `.hook`가 null이면 `null | test(...)` 에러. 모든 필터에 일괄 적용.
> - d0-plan은 OR 조건 단일 `select(... or ...)` 구조 — 원래 `select(...) // .[] | select(...)` 는 jq alternative operator 의미가 다르고 파이프 시작점이 의도대로 안 됨.
> - daily는 incident_repair.py가 이미 unresolved만 반환(라인 445 `if entry.get("resolved"): continue`)하므로 `.resolved == false` 조건은 redundant이지만 방어적으로 추가.

### finish.md (Phase 0 신설)
```markdown
### Phase 0: incident 사전 점검 (advisory)

```bash
python .claude/hooks/incident_repair.py --json --limit 5 \
  | jq '.[] | select((.hook // "") | test("commit_gate|auto_commit_state|final_check"))'
```
- **카테고리 필터**: `commit_gate` / `auto_commit_state` / `final_check` 계열만.
- 결과 1~3줄 인용 후 본문 진행. 차단 없음.
- 자동 수정 금지.
```

### daily.md (Phase 0 환경 준비 끝부분)
```markdown
4. **incident 사전 점검 (advisory)**
   ```bash
   python .claude/hooks/incident_repair.py --json --limit 5 \
     | jq --arg today "$(date +%Y-%m-%d)" \
       '.[] | select((.ts // "") | startswith($today)) | select((.resolved // false) == false)'
   ```
   - **필터**: 당일(KST) 발생 + unresolved.
   - 결과 인용 후 ZDM/MES 작업 진행. 차단 없음.
```

### d0-plan.md (자연어 트리거 다음, 첨부 파일 가드 위)
```markdown
## ⚠ incident 사전 점검 (advisory)

D0/OAuth/evidence_gate 미해결 건이 있으면 D0 흐름 진입 전 인용:
```bash
python .claude/hooks/incident_repair.py --json --limit 5 \
  | jq '.[] | select(
      ((.classification_reason // "") | test("evidence_missing|auth_diag|oauth|OAuth|D0"))
      or
      ((.hook // "") | test("evidence_gate|scheduler"))
    )'
```
- **필터**: `evidence_missing` / `auth_diag` / `oauth` / `D0` / `evidence_gate` / `scheduler` 계열 OR.
- 결과 인용 후 첨부 파일 가드로 진행. 차단 없음, 자동 수정 금지.
```

> 주의: incident_repair.py CLI에 `--filter` 옵션 없음(실측). jq 후처리 사용. Windows Git Bash에 jq 기본 포함 확인됨.

---

## 검증 방법

1. **변경 파일 목록**: `git status --porcelain` → 신규 1 + 수정 4. 그 외 0.
2. **새 hook 추가 없음**: `git diff --stat | grep -E "\.claude/hooks/|\.claude/settings"` → 출력 없음.
3. **final_check --fast PASS**: `bash .claude/hooks/final_check.sh --fast` → FAIL 0. (기존 WARN `python3 의존 잔존`은 무관).
4. **CLI 동작 실측**: `python .claude/hooks/incident_repair.py --json --limit 3` → JSON 배열 정상.
5. **jq 필터 실측**: `... | jq '.[] | select(.hook | test("commit_gate"))'` → 필터링 정상.
6. **토큰 비용**: `wc -c .claude/rules/incident_quote.md CLAUDE.md` → incident_quote ≤ 2KB, CLAUDE.md 증가 ≤ 200바이트.

---

## 롤백 방법

### 단순
```bash
git revert <commit-sha> --no-edit
git push origin main
```

### 수동
```bash
rm .claude/rules/incident_quote.md
git checkout HEAD~1 -- CLAUDE.md .claude/commands/finish.md .claude/commands/daily.md .claude/commands/d0-plan.md
bash .claude/hooks/final_check.sh --fast
git add -A && git commit -m "revert: incident_quote 규칙 롤백" && git push origin main
```

### 잔존 데이터 점검
- ERP/MES/SmartMES/Z드라이브: 해당 없음 (외부 호출 0).
- `.claude/incident_ledger.jsonl`: 수정 없음. 롤백 불필요.

---

## PASS 판정 기준 (사용자 합의)

- ✅ incident_quote.md는 기준 문서로만 추가
- ✅ CLAUDE.md는 링크 1줄 수준
- ✅ finish/daily/d0-plan은 incident 확인 안내만 추가
- ✅ auto-fix 자동 트리거 없음
- ✅ hook/settings 수정 없음
- ✅ final_check --fast PASS
- ✅ commit/push SHA 공유

---

## 다음 단계 (사용자 승인 후)

1. 4개 파일 수정/신설 (위 산출물 초안 그대로 반영)
2. final_check --fast 실행
3. 변경 SHA + git status 보고
4. 사용자 승인 후 commit + push
5. TASKS / HANDOFF / 도메인 STATUS 갱신 검토

**plan 위치 결정 (사용자 조건부 승인 4번 반영)**:
- 본 파일은 `.claude/plans/`(gitignore)에 작성됨.
- 새 폴더 신설 금지 (사용자 명시).
- **확정**: 기존 `90_공통기준/업무관리/_플랜/` 디렉토리에 `incident_quote_plan_20260430.md` 이름으로 commit 단계에서 이동.
- 415b09ce 선례(도메인 영역 이동)와 동일한 패턴, 폴더 신설 0건.
