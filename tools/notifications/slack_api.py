"""Unified Slack API – VELOS (dup‑skip + 콘솔 즉시 출력)"""

from __future__ import annotations
import os, json, time, hashlib, logging, pathlib, requests
from typing import Optional
from dotenv import load_dotenv

# ── .env 로드 ────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[2]       # giwanos
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT.parent / ".env", override=False)
# ────────────────────────────────────────────────────────────

TOKEN   = os.getenv("SLACK_BOT_TOKEN")
CHANNEL = os.getenv("SLACK_CHANNEL_ID") or os.getenv("SLACK_DEFAULT_CH")

_log = logging.getLogger("slack_api")

# 중복 전송 캐시
_recent: dict[str, float] = {}
TTL_SEC = 5          # 같은 메시지 5초 내 한 번

def _is_dup(sig: str) -> bool:
    now = time.time()
    _recent.update({k: v for k, v in _recent.items() if v >= now})
    if sig in _recent:
        return True
    _recent[sig] = now + TTL_SEC
    return False

def _post(text: str,
          channel: Optional[str] = None,
          blocks: Optional[list] = None) -> bool:
    ch = channel or CHANNEL
    if not TOKEN or not ch:
        msg = f"[Slack 전송 실패 ❌] TOKEN/CHANNEL 미설정 → {text}"
        print(msg); _log.warning(msg)
        return False

    sig = hashlib.md5(f"{ch}:{text}".encode()).hexdigest()
    if _is_dup(sig):
        msg = f"[Slack ⏩ Skip dup] {text}"
        print(msg); _log.info(msg)
        return True

    payload = {"channel": ch, "text": text}
    if blocks: payload["blocks"] = blocks

    try:
        res = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=5,
        )
        data = res.json()
        if data.get("ok"):
            msg = f"[Slack ✅] {text}"
            print(msg); _log.info(msg)
            return True
        msg = f"[Slack 전송 실패 ❌] {data.get('error')} → {text}"
        print(msg); _log.error(msg)
        return False
    except Exception as e:
        msg = f"[Slack 예외 ❌] {e} → {text}"
        print(msg); _log.exception(msg)
        return False

# 공용 API
def send(text: str, channel: str | None = None, blocks: list | None = None):
    return _post(text, channel, blocks)

def notify(text: str, channel: str | None = None, blocks: list | None = None):
    return _post(text, channel, blocks)

def post_message(text: str, channel: str | None = None, blocks: list | None = None):
    return _post(text, channel, blocks)

class SlackNotifier:
    def push(self, text: str, channel: str | None = None, blocks: list | None = None):
        return _post(text, channel, blocks)
