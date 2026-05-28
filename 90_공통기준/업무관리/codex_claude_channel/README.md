# Codex -> Claude Channels Bridge

## GUI auto_reply 운영 주의

- `auto_reply.py --target claude/codex`는 Windows GUI 창을 직접 찾아 paste + Enter를 수행한다.
- Codex 앱의 샌드박스 셸에서 일반 권한으로 실행하면 GUI 창 열거가 0개가 되어 `GUI_ACCESS_UNAVAILABLE` 또는 `window not found`가 날 수 있다.
- 이 경우 완료/진행 회신 실패로 확정하지 말고, 같은 명령을 Codex tool 실행 옵션 `sandbox_permissions=require_escalated`로 1회 재시도한다.
- `require_escalated` 재시도도 실패할 때만 `review.md` fallback을 최종 안전망으로 남긴다.

## 목적

`claude --resume -p` 외부 전송이 정책으로 차단될 때, Claude Code 공식 Channels 방식으로 Codex 검토 요청을 실행 중인 Claude 세션에 주입한다.

비유: 기존 방식은 다른 사무실로 문서를 택배 발송하는 구조였고, Channels는 같은 PC 안에 열린 창구로 접수시키는 구조다.

## 전제

- Claude Code Channels 기능이 계정/조직에서 활성화되어 있어야 한다.
- Claude Code v2.1.80 이상이 필요하다.
- Team/Enterprise 조직은 `channelsEnabled: true` 정책이 필요할 수 있다.
- 이 브리지는 개발 중인 로컬 MCP 서버이므로 Claude 실행 시 `--dangerously-load-development-channels server:codex-bridge`가 필요하다.

## 1회 설치

네트워크가 가능한 상태에서 한 번만 실행한다.

```powershell
$channelDir = "90_공통기준\업무관리\codex_claude_channel"
$tmp = Join-Path $channelDir ".tmp"
$cache = Join-Path $channelDir ".bun-cache"
New-Item -Path $tmp -ItemType Directory -Force | Out-Null
New-Item -Path $cache -ItemType Directory -Force | Out-Null
$env:TEMP = (Resolve-Path $tmp).Path
$env:TMP = (Resolve-Path $tmp).Path
bun install --cwd $channelDir --cache-dir (Resolve-Path $cache).Path --backend=copyfile --no-summary
```

## Claude 시작

```powershell
90_공통기준\업무관리\codex_claude_channel\start_claude_channel.ps1
```

이 명령은 Claude를 다음 조건으로 시작한다.

- MCP config: `codex_claude_channel/.mcp.json`
- Channel server: `server:codex-bridge`
- 로컬 HTTP 접수 포트: `127.0.0.1:8791`

## Codex 요청 전송

```powershell
python 90_공통기준\업무관리\codex_claude_channel\send_request.py `
  --request 90_공통기준\업무관리\검토기록\runs\20260525_codex_claude_bridge\request.md `
  --review 90_공통기준\업무관리\검토기록\runs\20260525_codex_claude_bridge\review.md
```

성공 시 `review.md`에 channel send PASS가 기록되고, Claude가 `reply` 도구를 호출하면 같은 파일에 Claude 검토 결과가 추가된다.

## 검증 기준

- 코드 검증: `bun build server.ts --target=bun --outfile .tmp/server-check.js`
- Python CLI 검증: `python send_request.py --help`
- 접수창 확인: `Invoke-RestMethod http://127.0.0.1:8791/health` 결과에 `channel_ready=true`가 표시되어야 한다.
- 최종 운영 검증: Claude를 `start_claude_channel.ps1`로 시작한 뒤 `send_request.py`가 PASS를 남기고 Claude 답변이 `review.md`에 기록되어야 한다.

## 주의

- 이 서버는 Claude Code가 MCP 부모 프로세스로 붙은 상태에서 쓰는 Channels 서버다.
- 단독 백그라운드 HTTP 서버처럼 띄워서 최종 검증하지 않는다. 단, 포트가 열렸는지와 MCP 준비 여부는 `/health`로 확인한다.
- 조직 정책이 Channels를 막으면 MCP 도구는 연결되어도 channel 메시지가 Claude 대화에 도착하지 않을 수 있다.
