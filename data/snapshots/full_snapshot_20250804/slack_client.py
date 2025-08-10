"""
Unified Slack client (bot‑token).  
env vars required:
  SLACK_BOT_TOKEN   xoxb‑***
  SLACK_DEFAULT_CH  #velos-notify  (channel name or ID)
"""
import os, logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

_TOKEN   = os.getenv("SLACK_BOT_TOKEN")
_CHANNEL = os.getenv("SLACK_DEFAULT_CH", "#general")
_client  = WebClient(token=_TOKEN)
_log     = logging.getLogger("slack_client")

def send(text: str,
         channel: str | None = None,
         blocks: list | None = None) -> None:
    if not _TOKEN:
        _log.warning("SLACK_BOT_TOKEN not set; skip Slack notify")
        return
    try:
        _client.chat_postMessage(
            channel=channel or _CHANNEL,
            text=text,
            blocks=blocks
        )
        _log.info("Slack notify OK → %s", channel or _CHANNEL)
    except SlackApiError as e:
        _log.error("Slack error: %s", e.response.get('error'))


