# settings 재분류 인벤토리 — 2026-04-19

> 의제5 3자 토론 합의(Round 1 pass_ratio 1.33) 쟁점 G "settings.local.json 공용화 구조 문제" 세션71 Phase 2-A 산출물.
> **본 인벤토리는 재분류 제안이며, 실제 파일 이동·병합은 세션72 별건**이다 (GPT 보강 수용).
> 로그: `90_공통기준/토론모드/logs/debate_20260418_190429_3way/`.

## 1. 현재 구조 (의제5 정리 후)

| 파일 | 항목 수 | 커밋 대상 | 현재 역할 |
|------|--------|----------|----------|
| `.claude/settings.json` | 3 (전역) | Yes (Git) | `permissions.allow` 3개 + hooks 없음 |
| `.claude/settings.local.json` | 95 (정리 후) | Yes (Git) | 프로젝트 전역 permissions + hooks 36개 + statusLine |

**문제**: `settings.local.json`에 팀 공용 정책(permissions·hooks 전역 규칙)과 개인·세션성 허용이 혼재. 공식 가이드상 `.local.json`은 로컬 프로젝트 설정 — Git 커밋 기본 원본 아님.

## 2. 재분류 제안 (쟁점 G 합의안)

### 2-A. 팀 공용 정책 → `.claude/settings.json` 이동 대상
Git 추적 필요, 모든 개발자/세션 공유 규칙.

**permissions.allow (예시 40+항목)**:
- 기본 도구: `Read`, `Write`, `Edit`, `MultiEdit`, `Glob`, `Grep`, `WebSearch`, `WebFetch`
- git 계열: `Bash(git *:*)`, `Bash(git add:*)`, `Bash(git commit:*)`, `Bash(git push:*)`, `Bash(gh *:*)`
- 파일 탐색 fallback: `Bash(ls:*)`, `Bash(wc:*)`, `Bash(find:*)`, `Bash(grep:*)`, `Bash(cat:*)`, `Bash(head:*)`, `Bash(tail:*)`, `Bash(echo:*)`
- 공통 런타임: `Bash(python3:*)`, `Bash(python:*)`, `Bash(node:*)`, `Bash(npm:*)`
- 프로젝트 hook 호출: `Bash(bash .claude/hooks/*:*)`, `Bash(source .claude/hooks/*:*)`
- 공통 스킬 경로: `Bash(python3 "90_공통기준/스킬/*":*)`, `Bash(python3 "90_공통기준/업무관리/운영검증/scripts/*":*)`
- MCP 공통: notion, gcal, Claude_in_Chrome 주요 도구들

**hooks 섹션 전체**: SessionStart·PreCompact·UserPromptSubmit·PreToolUse·PostToolUse·Notification·Stop 모든 매처

**statusLine**: `.claude/hooks/statusline.sh`

### 2-B. 개인·세션성 예외 → `.claude/settings.local.json` 유지 또는 gitignore
- 탭 ID 하드코딩 (현재는 `permissions_sanity.sh`가 경고로 감지, 포괄 패턴 `Bash(echo:*)` 흡수)
- 특정 파일 경로 rm/rmdir 일시 허용 (예: 테스트 중 생성된 XLSX)
- 로컬 환경 전용 powershell/tasklist 명령

### 2-C. 삭제 대상 (의제5 Phase 2-A 완료)
- 1회용 PID echo 8건, URL echo 3건, rm 3건, rmdir 1건, sed 1건 → **이미 제거**
- 완전 중복 2건 (Bash(cat:*), Bash(echo:*)) → **이미 제거**

## 3. 실물 이동 계획 (세션72 별건)

### Step 1: `.claude/settings.json` 확장
- 팀 공용 permissions 40+ 항목 이동
- hooks 섹션 전체 이동 (현재 local에만 존재)
- statusLine 이동

### Step 2: `.claude/settings.local.json` 축소
- 공용 항목 제거, 개인·세션성 예외만 잔존
- 최종 크기 목표: 10-20 항목 이내

### Step 3: gitignore 정책 결정
- 옵션 A: `.local.json` 자체를 gitignore (Claude Code 공식 권장)
- 옵션 B: `.local.json`도 Git 커밋 유지하되 세션성 예외로 명시

### Step 4: 검증
- `permissions_sanity.sh` 실행 → 경고 0건 유지
- `doctor_lite.sh` OK
- `smoke_fast.sh` 9/9 PASS
- 첫 세션 재시작 후 permissions 팝업 빈도 측정

## 4. 우선순위 & 차단 조건
- **우선순위**: 쟁점 G는 의제4 `/debate-verify` 실행 순서 재평가와 병행 가능. 세션72 의제로 이월.
- **차단 조건**: hooks 섹션 이동 시 경로 참조(`bash .claude/hooks/*`) 무결성 필수. 이동 중 훅 실패는 gate 등급이므로 세션 차단 유발 가능 → 단일 커밋으로 원자적 이동 필요.

## 5. 관련 문서
- `CLAUDE.md` → "hook vs permissions 역할 경계" 섹션 (2026-04-19 추가)
- `.claude/hooks/README.md` → "훅 등급 분류" 섹션 (2026-04-19 추가)
- `90_공통기준/토론모드/logs/debate_20260418_190429_3way/result.json` — 합의 원본

## 6. 현재 항목 분포 (의제5 정리 후, Python 집계)
```
settings.local.json allow: 95
  - 기본 도구(Read/Write/Edit 등): 8
  - Bash dedicated fallback (ls/wc/find/grep/cat/head/tail/echo): 8
  - git/gh 계열: 6
  - 공통 런타임 (python/bash/sleep 등): 약 20
  - 프로젝트 hook/스킬 경로: 약 30
  - MCP 도구: 약 15
  - 기타 특수 (powershell/tasklist 등): 약 8
```
→ 대부분 팀 공용 성격. 개인·세션성은 5-10개 이하로 추정. 실제 이동 시 각 항목 라벨링 필요.
