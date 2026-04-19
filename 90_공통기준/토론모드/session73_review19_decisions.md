# 쟁점 G Pre-Work — 세션73 (2026-04-19)

> 의제5 3자 토론 합의(Round 1 pass_ratio 1.33) 쟁점 G "settings.local.json 공용화 구조 문제"의 **세션74 실물 분리 사전작업**. 세션72 인벤토리(`settings_inventory_20260419.md`) 이후 permissions allow가 95→100건으로 확장되었고, 이 문서는 세션74 단일 원자 커밋 시 참조할 분류 결정표를 제공한다.
>
> 로그 원본: `debate_20260418_190429_3way/result.json`.

---

## 1. 현 상태 재확인 (세션73 시점)

| 항목 | 건수 | 위치 | 비고 |
|------|------|------|------|
| 전체 `permissions.allow` | 100 | `.claude/settings.local.json` | 세션72 기준 95→세션73 100 |
| hooks 이벤트 매처 | 31 | 동 파일 `hooks` 섹션 | PreToolUse 16 / PostToolUse 7 / Stop 4 / SessionStart·PreCompact·UserPromptSubmit·Notification 각 1 |
| `statusLine` | 1 | 동 파일 `statusLine` | `bash .claude/hooks/statusline.sh` |
| `.claude/settings.json` | — | 프로젝트 로컬 **없음** | 글로벌 `~/.claude/settings.json`만 존재 (env·플러그인·3개 개인 권한) |
| `.gitignore` 정책 | 적용 | `.claude/settings.local.json` 제외 | 옵션 A 이미 반영 |

---

## 2. Permissions 100건 분류 결정표

세션73 탐색으로 확정.

### 2-1. TEAM (→ `.claude/settings.json`로 이동) — 66+14=80건

팀 공용 정책. Git 커밋 대상. 모든 개발자·세션 공유.

| 소분류 | 건수 | 대표 항목 |
|-------|-----|----------|
| Basic Tools | 8 | `Read`, `Write`, `Edit`, `MultiEdit`, `Glob`, `Grep`, `WebSearch`, `WebFetch` |
| Read 경로 | 1 | 프로젝트 루트 Read(...) |
| Git/GH | 5 | `Bash(git *:*)`, `Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git push:*)`, `Bash(gh *:*)` |
| Bash fallback 13 | 13 | `Bash(ls:*)`, `Bash(wc:*)`, `Bash(find:*)`, `Bash(grep:*)`, `Bash(cat:*)`, `Bash(head:*)`, `Bash(tail:*)`, `Bash(echo:*)`, `Bash(mkdir:*)`, `Bash(tar:*)`, `Bash(gzip:*)`, `Bash(curl:*)`, `Bash(do echo:*)` |
| Common Runtime | 2 | `Bash(bash -n:*)`, `Bash(claude config:*)` |
| Runtime | 1 | `Bash(python3:*)` |
| Project Hooks/Scripts/Commands | 13 | `Bash(bash .claude/hooks/*:*)`, `Bash(source .claude/hooks/*:*)`, `Bash(bash .claude/scripts/*:*)`, 등 |
| Project Skills | 6 | `Bash(python "90_공통기준/스킬/*":*)` 등 |
| MCP 공통 | 17 | gcal / notion / scheduled-tasks 주요 도구 |
| **추가 — REVIEW 승격** | 14 | `Bash(TZ=Asia/Seoul date*:*)`, `Bash(for f:*)`, `Bash(done)`, `Bash(python3 -c ':*)`, `Bash(python3)`, `Bash(python -c ':*)`, `Bash(date -u ...)`, `Bash(python3 -c ' *)`, `Bash(awk -F'"ts":"' ...)`, `Bash(awk -F'"' ...)`, `Bash(python3 -c "import json*:*)`, `Bash(cat .claude/state/*:*)`, `Bash(PYTHONUTF8=1 python3)`, `Bash(python3 -c '...')` |

**분류 근거**:
- `TZ=Asia/Seoul date`는 한국 제조업 환경의 팀 공용 타임존 유틸 — TEAM
- `bash -n`/`for f`/`done`은 모든 셸 스크립팅에서 쓰는 제어 구문 — TEAM
- `python3 -c '...'`류는 범용 스니펫. 개인 경로 없으면 TEAM
- `awk -F'"' ...` 등 파싱 패턴은 JSON/CSV 처리 공용 — TEAM
- `cat .claude/state/*`는 프로젝트 상대 경로 — TEAM
- `PYTHONUTF8=1 python3`는 한글 환경 공용 설정 — TEAM

### 2-2. PERSONAL (→ `.claude/settings.local.json` 유지) — 4건

| 소분류 | 건수 | 항목 |
|-------|-----|------|
| Windows 전용 OS 도구 | 3 | `Bash(powershell -Command Get-Date:*)`, `Bash(tasklist:*)`, `Bash(schtasks:*)` |
| Windows `start` 명령 | 1 | `Bash(start *:*)` |

**분류 근거**:
- Windows 로컬 환경에서만 유효. 팀원이 macOS·Linux를 쓰면 실행 불가 → PERSONAL
- `wmic process *`는 세션73 시점 `.local.json`에 이미 있음(WindowsTool) → PERSONAL로 유지

### 2-3. PERSONAL + 사용자 설정 (→ `.claude/settings.json` 저장은 부적절) — 11건

절대경로 `C:/Users/User/...`가 포함되어 이 머신 전용.

| 건수 | 예시 |
|-----|------|
| 11 | `Bash(mkdir -p "C:/Users/User/.../...")`, `Bash(git -C "C:/Users/User/..." rev-parse HEAD)`, `Bash(python3 "C:/Users/User/...")` 등 |

**분류 근거**: 개인 머신 경로 하드코딩. 팀공유 불가 → PERSONAL
**제거 권장**: 대부분 프로젝트 상대경로로 대체 가능. 세션74 실물 분리 시 `mkdir -p "C:/..."` 항목 11건을 **삭제**하고 프로젝트 상대경로 재발행 권장.

### 2-4. DELETE (1회용 잔재 — 양쪽 모두에서 제거) — 3건

`permissions_sanity.sh`가 감지하지 못한 잔재. regex가 double-quote만 매칭 — **single-quote 버전 미탐지 버그** 발견.

| 항목 | 삭제 사유 | 포괄 패턴 대체 |
|------|----------|---------------|
| `Bash(echo 'https://chatgpt.com/...')` | 1회용 URL echo | `Bash(echo:*)` 이미 TEAM에 있음 |
| `Bash(echo '1382935544')` | 1회용 PID echo | `Bash(echo:*)` 이미 TEAM에 있음 |
| `Bash(PYTHONUTF8=1 python3 -c "import json; d=json.load(open('.claude/settings.local.json'...))")` | 1회용 검증 스크립트 | `Bash(PYTHONUTF8=1 python3)` + `Bash(python3 -c ':*)` 포괄로 커버 |

### 2-5. permissions_sanity.sh 버그 리포트 (부수 발견)

```python
# 현재 regex (settings73 탐색 중 발견)
(re.compile(r'^Bash\(echo "\d{10,}"\)$'), 'PID echo 하드코딩'),
(re.compile(r'^Bash\(echo "https?://.*"\)$'), 'URL echo 하드코딩'),
```
- 위 정규식은 **double-quote(`"`)만 매칭**. single-quote(`'`) 변형 미탐지
- 세션73 시점 실제 잔재: `Bash(echo 'https://...')`, `Bash(echo '1382935544')`
- **수정 방향** (세션74+): `["\']` 으로 양쪽 따옴표 모두 허용
- 이 버그는 세션74 settings 분리 이전에 수정되는 것이 이상적 (새 settings.json 생성 시 이 패턴들이 다시 들어가지 않도록)

---

## 3. 분류 기준 원칙 (신규 추가)

세션73 이후 새 항목 분류 시 적용.

| 조건 | 분류 |
|-----|------|
| Windows 전용 OS 도구 (powershell, tasklist, schtasks, wmic, start) | PERSONAL |
| 개인 인증에 묶인 CLI (gemini, 개인 GH token 등) | PERSONAL |
| 절대경로 `C:/Users/User/` 또는 `/home/user/` 포함 | PERSONAL |
| 프로젝트 상대경로 (`.claude/*`, `90_공통기준/*` 등) | TEAM |
| 언어 런타임 일반 플래그 (`python -c`, `node -e`, `awk -F`) | 스니펫에 절대경로 없으면 TEAM |
| macOS/Linux 도구 (`pkill`, `pgrep` 등) | 크로스플랫폼이면 TEAM, macOS/Linux 전용이면 PERSONAL |
| 제어 구문 (`for`, `done`, `if`, `then`) | TEAM |
| 타임존·인코딩 유틸 (`TZ=`, `PYTHONUTF8=`, `date -u`) | TEAM (프로젝트 한글 환경 기본) |
| 포괄 패턴이 이미 있는 1회용 하드코딩 | **DELETE** |

---

## 4. gate 9개 `exit 2` 승격 기준선 (Phase 2-C 1주 관찰 대상)

세션73 커밋 B에서 timing만 배선. `exit 2` 승격은 `hook_timing.jsonl` 1주 수집 후 판단. 승격 판단은 세션75+.

| 훅 | 이벤트/매처 | 현재 exit | 승격 검토 기준 | 세션73 결정 |
|---|---|---|---|---|
| `harness_gate.sh` | PreToolUse/Bash | 0 | 1주 내 `block_incomplete`/`block_notranscript` status 빈도 ≥ 3회 | 보류 |
| `evidence_gate.sh` | PreToolUse/Write\|Edit\|MultiEdit | 0 | `block_*` status ≥ 3회 + bypass 시도 로그 | 보류 |
| `mcp_send_gate.sh` | PreToolUse/mcp_form_input | 0 | `block_missing` status ≥ 2회 | 보류 |
| `instruction_read_gate.sh` | PreToolUse/Bash | 0 | 지침 미독 incident ≥ 2회 | 보류 |
| `skill_instruction_gate.sh` | PreToolUse/Bash | 0 | MES/ZDM 접근 차단 bypass | 보류 |
| `debate_gate.sh` | PreToolUse/mcp_js_tool | 0 | debate 우회 incident ≥ 1회 | 보류 |
| `debate_independent_gate.sh` | PreToolUse/mcp_js_tool | 0 | 독립견해 미첨부 bypass | 보류 |
| `navigate_gate.sh` | PreToolUse/mcp_navigate | 0 | 지침 미독 chatgpt 진입 bypass | 보류 |
| `gpt_followup_stop.sh` | Stop | 0 | pending flag 미소비 누적 | 보류 |

**판단 원칙**:
- `hook_timing.jsonl` 1주 수집 전에는 승격 금지 — 거짓 deny 빈도 미측정
- JSON deny(`hookSpecificOutput.permissionDecision: "deny"`)가 이미 차단 역할. `exit 2` 추가는 stderr 표시 차이만 있음
- `exit 2` 승격은 "Claude 또는 harness가 JSON 결정을 무시하는 사례가 실측됐을 때"만 정당화

**승격 절차 (세션75+ 가이드)**:
1. `hook_timing.jsonl` 7일치 집계 — 해당 훅의 `status=block_*` 빈도 확인
2. `incident_ledger.jsonl`에서 해당 훅 관련 `gate_reject`/`hook_block` 조회
3. Claude가 JSON deny를 무시한 실증 사례 1건 이상 확인
4. 조건 충족 시 `exit 2` 승격 (hook_common.sh 표준 패턴 사용)

---

## 5. 세션74 실물 분리 절차

### Step 1: `.claude/settings.json` 신규 생성
- TEAM 80건 `permissions.allow`
- hooks 섹션 전체 이동 (31 매처, 상대경로 확보)
- statusLine 이동

### Step 2: `.claude/settings.local.json` 축소
- PERSONAL 4건 + 사용자경로 11건 = 15건만 유지 (C:/경로는 세션74에서 제거 여부 재판단 — 권장: 프로젝트 상대경로 대체)
- DELETE 3건 제거
- hooks·statusLine 제거

### Step 3: `.gitignore` 확인
- 이미 `.claude/settings.local.json` 제외 적용 (옵션 A) — 추가 작업 없음

### Step 4: `permissions_sanity.sh` 버그 수정 (선택)
- regex `["\']` 으로 single-quote 포함 매칭 추가
- 본 커밋에 포함 가능 or 별건

### Step 5: 원자 커밋 + 세션 재시작 **필수**
- 단일 커밋으로 settings.json 신설 + settings.local.json 축소 반영
- 세션 재시작 없이 새 settings 미반영 (Claude Code 캐싱 특성)

### Step 6: 재시작 후 검증
- `/doctor_lite` — hooks 매처 로드 확인
- `/smoke_fast` — 9/9 PASS
- `/permissions_sanity` — 경고 0건 (DELETE 3건 제거 + regex 버그 수정 후)
- 1주 후 permissions 팝업 빈도 측정 — 분리 효과 확인

---

## 6. 롤백 전략

### 세션74 세션 차단 발생 시
1. Claude Code CLI 강제 종료 (Taskkill 또는 창 닫기)
2. 외부 Git Bash에서:
   ```
   cd "C:\Users\User\Desktop\업무리스트"
   git log --oneline -5
   git revert <settings-commit>
   ```
3. Claude Code CLI 재시작
4. `/doctor_lite` 로 복구 확인

**금지 사항**:
- `git reset --hard` (다른 작업 손실 위험)
- 훅 파일 수동 rename (원자 커밋 파괴)
- 세션 재시작 건너뛰기 (설정 미반영 상태 위험)

---

## 7. 관련 문서

- `90_공통기준/토론모드/settings_inventory_20260419.md` — 세션72 원본 인벤토리(95건 기준)
- `CLAUDE.md` → "hook vs permissions 역할 경계" 섹션
- `.claude/hooks/README.md` → Phase 2-B/2-C 적용 현황 테이블
- `.claude/hooks/permissions_sanity.sh` → 1회용/중복 탐지 advisory(세션71 신설, 버그 수정 세션74 검토)
- `debate_20260418_190429_3way/result.json` — 의제5 합의 원본
