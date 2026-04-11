# .claude 공유 정책

이 폴더는 Claude 실행 규칙과 로컬 세션 상태가 함께 섞이기 쉬운 구간이다.  
공유 문서와 로컬 상태를 아래 기준으로 분리한다.

## Git 추적 대상

- `rules/*.md`
- `commands/*.md`
- `hooks/README.md`
- `.claude/README.md`

위 파일은 팀 공통 규칙, 명령 문서, 훅 구조 설명처럼 세션 간 공유가 필요한 자산만 둔다.

## 로컬 전용 상태

아래 항목은 세션 상태, 로그, 개인 설정으로 보고 커밋하지 않는다.

- `settings.local.json`
- ~~`incident_ledger.jsonl`~~ → **Git 추적 유지** (세션15 정책 확정: 감사 로그로 원격 검증에 활용)
- `command-audit.log`
- `subagent-audit.log`
- `tool-failure.log`
- `launch.json`
- `state/`
- `plans/`
- `logs/`
- `hooks/hook_log.jsonl`
- `hooks/skill_usage.jsonl`
- `hooks/.notify_dedup`
- `hooks/send_gate_passed`

## 운영 원칙

1. `.claude` 안에 새 공유 문서를 추가할 때는 `.gitignore` 예외 규칙도 같이 점검한다.
2. 세션 URL, 토큰, 로컬 경로 캐시, 디버그 로그는 공유 문서에 남기지 않는다.
3. 실행 규칙은 `rules/`, 명령 설명은 `commands/`, 구조 설명은 `README.md` 계열에 둔다.
4. Windows에서 Bash가 필요하면 `.claude/scripts/run_git_bash.ps1 '<command>'`를 기본 경로로 사용한다. `bash`가 PATH에 없더라도 Git Bash 절대경로로 실행된다.
