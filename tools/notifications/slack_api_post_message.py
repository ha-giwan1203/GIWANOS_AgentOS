# =============================================
# VELOS: Slack Test CLI
# =============================================
from __future__ import annotations
import argparse
from modules.core.slack_client import SlackClient

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True, help="보낼 메시지")
    ap.add_argument("--channel", default=None)
    args = ap.parse_args()
    SlackClient().send_message(args.channel or "", args.test)
    print('{"ok": true}')

if __name__ == "__main__":
    main()
