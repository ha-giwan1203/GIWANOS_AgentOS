import os
import sys
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos"))
ENV = ROOT / "configs" / ".env"
if not ENV.exists():
    print(f"[ERR] no .env: {ENV}")
    sys.exit(1)
load_dotenv(ENV)

tok = os.getenv("SLACK_BOT_TOKEN", "")
ch = os.getenv("SLACK_CHANNEL_ID") or os.getenv("SLACK_SUMMARY_CH") or os.getenv("SLACK_CHANNEL")
print("[ENV] token_prefix:", tok[:6], "len:", len(tok))
print("[ENV] channel:", ch)

hdr = {"Authorization": f"Bearer {tok}"}


def call(method, **kw):
    r = requests.post(f"https://slack.com/api/{method}", headers=hdr, data=kw, timeout=15)
    try:
        j = r.json()
    except Exception:
        j = {"raw": r.text}
    print(f"[API] {method} ->", json.dumps(j)[:400])
    return j


# 1) 토큰 실명
auth = call("auth.test")
bot_user_id = auth.get("bot_id") or auth.get("user_id")
team = auth.get("team")
print("[AUTH] bot_user_id:", bot_user_id, "team:", team)

# 2) 채널 확인
if ch and ch.startswith("C"):
    call("conversations.info", channel=ch)
    call("conversations.members", channel=ch, limit=100)
else:
    print("[HINT] SLACK_CHANNEL_ID가 C로 시작하는 공개 채널 ID인지 확인 필요")

# 3) 메서드 가용성 샘플 콜
call("files.uploadV2")  # 의도적으로 파라미터 없이 호출 -> error code 확인용
call("files.getUploadURLExternal", filename="probe.txt", length=5)
