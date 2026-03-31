# Settings Allow 패턴 요약 (2026-04-01 정리)

> settings.local.json은 토큰 포함으로 git 불가. 이 요약본만 git에 올림.

## 총 46개 (172개에서 정리)

### 읽기성 명령 (12개)
git status/diff/log/branch, ls, wc, find, grep, cat, head, tail, echo

### git 변경성 (4개)
git add, git commit, git push, gh pr

### python (7개)
python3, python -c, python3 -c, PYTHONUTF8/PYTHONIOENCODING 변형, pip install

### 셸 유틸리티 (7개)
chmod, mkdir, cp, mv, sleep, tar, bash

### 시스템 (2개)
taskkill /f /im EXCEL.EXE, cmd /c

### Read (5개)
/tmp, Desktop, 업무리스트, .claude/projects, .claude

### MCP (2개)
gcal_create_event, notion-update-page

### Web (6개)
WebSearch, WebFetch 5개 도메인

## 보안 조치
- curl에 하드코딩된 GitHub OAuth 토큰 제거
- powershell은 개별 명령만 허용 (와일드카드 안 씀)
- python은 접두사 매칭이라 경로 제한 적용

## 백업
settings.local.json.bak_20260401
