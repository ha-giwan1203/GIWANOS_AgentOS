# [ACTIVE] scripts/dispatch_email.py
from __future__ import annotations

import json
import mimetypes
import os
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

# --- 환경변수 로딩 ---
try:
    from env_loader import load_env

    load_env()
except ImportError:

    def _load_dotenv():
        try:
            from dotenv import load_dotenv
        except Exception:
            return
        root = Path(r"C:\giwanos")
        for p in (root / "configs/.env", root / ".env"):
            if p.exists():
                load_dotenv(dotenv_path=p, override=False, encoding="utf-8")

    _load_dotenv()

ROOT = Path(r"C:\giwanos")
AUTO = ROOT / "data" / "reports" / "auto"
DISP = ROOT / "data" / "reports" / "_dispatch"
DISP.mkdir(parents=True, exist_ok=True)


def _env(name, default=None):
    return os.getenv(name, default)


# 호환 매핑
SMTP_HOST = _env("SMTP_HOST") or _env("EMAIL_HOST")
SMTP_PORT = _env("SMTP_PORT") or _env("EMAIL_PORT") or "587"
SMTP_USER = _env("SMTP_USER") or _env("EMAIL_USER")
SMTP_PASS = _env("SMTP_PASS") or _env("EMAIL_PASSWORD")


def send_email_only(pdf_path: Path, subject: str, body: str) -> dict:
    """Email 전용 전송 함수"""
    if not _env("DISPATCH_EMAIL", "1") == "1":
        return {"ok": False, "detail": "disabled", "ts": int(time.time())}

    host = SMTP_HOST
    port = int(SMTP_PORT)
    user = SMTP_USER
    pw = SMTP_PASS
    to = (_env("EMAIL_TO") or "").split(",")
    sender = _env("EMAIL_FROM") or user

    if not (host and user and pw and to and sender):
        return {"ok": False, "detail": "missing SMTP configs", "ts": int(time.time())}

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join([t.strip() for t in to if t.strip()])
        msg.set_content(body, charset="utf-8")

        # UTF-8 인코딩 강제 설정
        import locale
        import sys

        sys.stdout.reconfigure(encoding="utf-8")
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

        ctype, _ = mimetypes.guess_type(str(pdf_path))
        maintype, subtype = (ctype or "application/pdf").split("/", 1)
        # 파일명을 안전하게 처리
        safe_filename = pdf_path.name.encode("ascii", "ignore").decode("ascii")
        msg.add_attachment(
            pdf_path.read_bytes(), maintype=maintype, subtype=subtype, filename=safe_filename
        )

        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
        return {"ok": True, "detail": "sent", "ts": int(time.time())}
    except Exception as e:
        return {"ok": False, "detail": f"exception: {e}", "ts": int(time.time())}


def dispatch_email():
    """Email 디스패치 메인 함수"""
    # 테스트 보고서 우선 사용
    latest = max(AUTO.glob("velos_test_report_*.pdf"), default=None)
    if not latest:
        # 기존 보고서 사용
        latest = max(AUTO.glob("velos_auto_report_*_ko.pdf"), default=None)
        if not latest:
            print("no pdf found in", AUTO)
            return False

    subject = "VELOS Test Report"
    safe_filename = latest.name.replace("_ko", "_en").replace("_test_", "_test_")
    body = f"VELOS Test Report\nFile: {safe_filename}"

    result = send_email_only(latest, subject, body)

    # 결과 저장
    out = DISP / f"dispatch_email_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # 결과 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result["ok"]


if __name__ == "__main__":
    success = dispatch_email()
    exit(0 if success else 1)
