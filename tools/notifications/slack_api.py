"""Unified Slack API – VELOS (v2).
Improvements:
- TTL_SEC configurable via SLACK_DUP_TTL environment variable
- Logging unified (no print)
- Fallback to DM (self) when channel omitted
"""
from __future__ import annotations
import os, json, time, hashlib, logging, pathlib, requests
from typing import Optional
from dotenv import load_dotenv

# ── .env 로드 ────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[2]       # giwanos
load_dotenv(ROOT / "configs" / ".env", override=False)
load_dotenv(pathlib.Path.home() / ".velos.env", override=True)
# ────────────────────────────────────────────────────────────

TOKEN   = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_DEFAULT = os.getenv("SLACK_CHANNEL_ID") or os.getenv("SLACK_DEFAULT_CH")

TTL_SEC = int(os.getenv("SLACK_DUP_TTL", "5"))      # duplicate‑skip window
_log = logging.getLogger("velos.slack")

# Deduplicate cache
_recent: dict[str, float] = {}

def _is_dup(sig: str) -> bool:
    now = time.time()
    # purge old
    for k in list(_recent.keys()):
        if _recent[k] < now:
            _recent.pop(k, None)
    if sig in _recent:
        return True
    _recent[sig] = now + TTL_SEC
    return False

def _call_slack_api(method: str, payload: dict) -> dict:
    resp = requests.post(
        f"https://slack.com/api/{method}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        data=json.dumps(payload),
        timeout=5
    )
    try:
        return resp.json()
    except Exception:
        return {"ok": False, "error": "json_parse_fail"}

def _resolve_dm_channel() -> Optional[str]:
    # Open IM channel with self if not cached
    if not TOKEN:
        return None
    data = _call_slack_api("auth.test", {})
    user_id = data.get("user_id")
    if not user_id:
        return None
    im = _call_slack_api("conversations.open", {"users": user_id})
    return im.get("channel", {}).get("id")

def _post(text: str, channel: Optional[str] = None, blocks: Optional[list] = None) -> bool:
    ch = channel or CHANNEL_DEFAULT or _resolve_dm_channel()
    if not TOKEN or not ch:
        _log.warning("Slack TOKEN or channel not set → message dropped: %s", text)
        return False

    sig = hashlib.md5(f"{ch}:{text}".encode()).hexdigest()
    if _is_dup(sig):
        _log.info("Slack dup‑skip: %s", text)
        return True

    payload = {"channel": ch, "text": text}
    if blocks:
        payload["blocks"] = blocks

    res = _call_slack_api("chat.postMessage", payload)
    if res.get("ok") is True:
        _log.info("Slack ✅ %s", text)
        return True
    _log.error("Slack ❌ %s -> %s", res.get("error"), text)
    return False

# public helpers
def send(text: str, channel: str | None = None, blocks: list | None = None):
    return _post(text, channel, blocks)

notify = post_message = send

class SlackNotifier:
    def push(self, text: str, channel: str | None = None, blocks: list | None = None):
        return _post(text, channel, blocks)
