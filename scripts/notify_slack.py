from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(r"C:\giwanos")
REPORTS = ROOT / r"data\reports"
ENV = ROOT / r"configs\.env"


def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def latest_pdf():
    files = list(REPORTS.glob("velos_report_*.pdf"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def main():
    load_env()
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("[SKIP] SLACK_WEBHOOK_URL 미설정")
        return 0
    p = latest_pdf()
    if not p:
        print("[SKIP] 최신 PDF 없음")
        return 0
    text = f"VELOS 보고서 생성: {p.name}\\n경로: {p}"
    body = json.dumps({"text": text}).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urlopen(req).read()
        print("[OK] Slack 알림 전송")
    except Exception as e:
        print("[WARN] Slack 전송 실패:", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
