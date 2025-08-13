# probe_slack.ps1 — venv + .env 적용 후 Slack 메시지 전송 테스트
param(
  [string] $Channel = "#general",
  [string] $Text    = "VELOS Slack probe"
)
$VenvPath    = "C:/Users/User/venvs/velos"
$EnvFilePath = "C:/Users/User/venvs/velos/.env"

$ErrorActionPreference = "Stop"
. "C:/giwanos/scripts/_venv_bootstrap.ps1" -VenvPath $VenvPath -EnvFilePath $EnvFilePath

$py = "$VenvPath/Scripts/python.exe"
& $py - <<'PY'
import os, sys
sys.path.append("C:/giwanos/scripts")
try:
    import notify_slack_api as api
except Exception as e:
    print("[err] import notify_slack_api:", e); sys.exit(1)

token = os.getenv("SLACK_BOT_TOKEN")
chan  = os.environ.get("CHAN") or "#general"
text  = os.environ.get("TEXT") or "VELOS probe"
if not token:
    print("[err] SLACK_BOT_TOKEN not set"); sys.exit(2)
api.send_message(token, chan, text)
print("[ok] sent to", chan)
PY
