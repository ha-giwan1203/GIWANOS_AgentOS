# [ACTIVE] VELOS 운영 철학: 파일명/경로 불변 · 거짓 코드 금지 · 자가 검증 · 로그 증빙
from __future__ import annotations

import json
import mimetypes
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(r"C:\giwanos")
HEALTH_PATH = ROOT / "data" / "logs" / "system_health.json"


def write_health(ok: bool, reason: str = "", targets=None):
    try:
        d = {}
        if HEALTH_PATH.exists():
            d = json.loads(HEALTH_PATH.read_text(encoding="utf-8") or "{}")
        d["dispatch_last_ok"] = bool(ok)
        d["dispatch_last_targets"] = list(
            sorted(set((targets or []) + (d.get("dispatch_last_targets") or [])))
        )
        d["dispatch_last_ts"] = datetime.now(timezone.utc).isoformat()
        if not ok:
            d["dispatch_last_error"] = reason
        tmp = HEALTH_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(HEALTH_PATH)
    except Exception:
        pass


def build_message(subject: str, body: str, sender: str, recipients: list[str], attach: list[str]):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body or "")
    for path in attach or []:
        p = Path(path)
        if not p.exists():
            continue
        ctype, enc = mimetypes.guess_type(p.name)
        maintype, subtype = ctype.split("/", 1) if ctype else ("application", "octet-stream")
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)
    return msg


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", required=False, default="")
    ap.add_argument("--attach", nargs="*", default=[])
    ap.add_argument("--to", nargs="*", default=[])
    args = ap.parse_args()

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT") or 587)
    user = os.getenv("SMTP_USER")
    pwd = os.getenv("SMTP_PASS")
    tls = os.getenv("SMTP_TLS", "1") == "1"
    sender = os.getenv("EMAIL_FROM")
    rcpts_env = [x.strip() for x in (os.getenv("EMAIL_TO") or "").split(",") if x.strip()]
    recipients = args.to or rcpts_env

    if not (host and user and pwd and sender and recipients):
        reason = "missing SMTP/EMAIL envs"
        print("[EMAIL] config error:", reason)
        write_health(False, reason, ["email"])
        return 70

    msg = build_message(args.subject, args.body, sender, recipients, args.attach)
    try:
        with smtplib.SMTP(host, port, timeout=20) as s:
            if tls:
                s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        print("[EMAIL] sent to", recipients)
        write_health(True, targets=["email"])
        return 0
    except Exception as e:
        reason = f"send failure: {e}"
        print("[EMAIL]", reason)
        write_health(False, reason, ["email"])
        return 72


if __name__ == "__main__":
    sys.exit(main())
