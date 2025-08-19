# [ACTIVE] scripts/dispatch_report.py
from __future__ import annotations
import os, json, time, smtplib, mimetypes
from pathlib import Path
from email.message import EmailMessage

# --- 환경변수 로딩 ---
def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    root = Path(r"C:\giwanos")
    for p in (root/"configs/.env", root/".env"):
        if p.exists():
            load_dotenv(dotenv_path=p, override=False, encoding="utf-8")
_load_dotenv()

try:
    import requests  # venv에 이미 있을 가능성 높음
    from modules.utils.net import post_with_retry, get_with_retry
except Exception:
    requests = None  # 없으면 해당 채널은 자동 스킵
    post_with_retry = None
    get_with_retry = None

ROOT   = Path(r"C:\giwanos")
AUTO   = ROOT / "data" / "reports" / "auto"
DISP   = ROOT / "data" / "reports" / "_dispatch"
DISP.mkdir(parents=True, exist_ok=True)

def _env(name, default=None):
    return os.getenv(name, default)

# 호환 매핑
SMTP_HOST = _env("SMTP_HOST") or _env("EMAIL_HOST")
SMTP_PORT = _env("SMTP_PORT") or _env("EMAIL_PORT") or "587"
SMTP_USER = _env("SMTP_USER") or _env("EMAIL_USER")
SMTP_PASS = _env("SMTP_PASS") or _env("EMAIL_PASSWORD")

PUSHBULLET_TOKEN = _env("PUSHBULLET_TOKEN") or _env("PUSHBULLET_API_KEY")

SLACK_WEBHOOK_URL = _env("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN   = _env("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID  = _env("SLACK_CHANNEL_ID") or _env("SLACK_CHANNEL")

def _result(ok: bool, detail: str) -> dict:
    return {"ok": ok, "detail": detail, "ts": int(time.time())}

# ---------------- Slack ----------------
def send_slack(pdf_path: Path, text: str) -> dict:
    if not _env("DISPATCH_SLACK", "1") == "1":
        return _result(False, "disabled")

    # Webhook URL 우선 사용
    webhook_url = SLACK_WEBHOOK_URL or _env("VELOS_SLACK_WEBHOOK")
    if webhook_url:
        try:
            payload = {
                "text": f"{text}\n파일 경로: {pdf_path}",
                "attachments": [{
                    "title": pdf_path.name,
                    "text": "VELOS 한국어 보고서가 생성되었습니다.",
                    "color": "good"
                }]
            }
            resp = post_with_retry(webhook_url, json=payload, timeout=20, retries=2) if post_with_retry else requests.post(webhook_url, json=payload, timeout=20)
            return _result(resp.status_code == 200, f"webhook: status={resp.status_code}")
        except Exception as e:
            return _result(False, f"webhook exception: {e}")

    # Bot Token 방식 (폴백)
    token = SLACK_BOT_TOKEN
    channel = SLACK_CHANNEL_ID
    if not (token and channel):
        return _result(False, "missing SLACK_BOT_TOKEN or SLACK_CHANNEL_ID")
    if requests is None:
        return _result(False, "requests not installed")
    try:
        # 메시지만 전송 (파일 업로드는 제외)
        resp = (post_with_retry(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            data={"channel": channel, "text": f"{text}\n파일 경로: {pdf_path}"},
            timeout=20,
            retries=2
        ) if post_with_retry else requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            data={"channel": channel, "text": f"{text}\n파일 경로: {pdf_path}"},
            timeout=20,
        )).json()
        return _result(bool(resp.get("ok")), f"chat.postMessage: {resp}")
    except Exception as e:
        return _result(False, f"exception: {e}")

# ---------------- Notion ----------------
def send_notion(pdf_path: Path, md_path: Path|None, title: str) -> dict:
    if not _env("DISPATCH_NOTION", "1") == "1":
        return _result(False, "disabled")
    token = _env("NOTION_TOKEN")
    database_id = _env("NOTION_DATABASE_ID")
    if not (token and database_id):
        return _result(False, "missing NOTION_TOKEN or NOTION_DATABASE_ID")
    if requests is None:
        return _result(False, "requests not installed")
    # 로컬 파일을 직접 올릴 수 없으니, 경로와 요약을 페이지에 남긴다.
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        props = {
            "제목": {"title": [{"text": {"content": title}}]},
            "설명": {"rich_text": [{"text": {"content": f"PDF 파일: {pdf_path.name}"}}]},
        }
        children = []
        if md_path and md_path.exists():
            snippet = (md_path.read_text("utf-8", errors="ignore")[:1200]).strip()
            if snippet:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type":"text","text":{"content": snippet}}]}
                })
        payload = {"parent": {"database_id": database_id}, "properties": props, "children": children}
        resp = post_with_retry("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), retries=2) if post_with_retry else requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        ok = resp.status_code < 300
        return _result(ok, f"status={resp.status_code}")
    except Exception as e:
        return _result(False, f"exception: {e}")

# ---------------- Email ----------------
def send_email(pdf_path: Path, subject: str, body: str) -> dict:
    if not _env("DISPATCH_EMAIL", "1") == "1":
        return _result(False, "disabled")
    host = SMTP_HOST; port = int(SMTP_PORT)
    user = SMTP_USER; pw = SMTP_PASS
    to   = (_env("EMAIL_TO") or "").split(",")
    sender = _env("EMAIL_FROM") or user
    if not (host and user and pw and to and sender):
        return _result(False, "missing SMTP configs")
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join([t.strip() for t in to if t.strip()])
        msg.set_content(body)

        ctype, _ = mimetypes.guess_type(str(pdf_path))
        maintype, subtype = (ctype or "application/pdf").split("/", 1)
        msg.add_attachment(pdf_path.read_bytes(), maintype=maintype, subtype=subtype, filename=pdf_path.name)

        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
        return _result(True, "sent")
    except Exception as e:
        return _result(False, f"exception: {e}")

# ---------------- Pushbullet ----------------
def send_pushbullet(title: str, body: str) -> dict:
    if not _env("DISPATCH_PUSH", "1") == "1":
        return _result(False, "disabled")
    token = PUSHBULLET_TOKEN
    if not token:
        return _result(False, "missing PUSHBULLET_TOKEN")
    if requests is None:
        return _result(False, "requests not installed")
    try:
        resp = post_with_retry(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": token, "Content-Type": "application/json"},
            data=json.dumps({"type":"note","title": title,"body": body}, ensure_ascii=False).encode("utf-8"),
            timeout=20,
            retries=2
        ) if post_with_retry else requests.post(
            "https://api.pushbullet.com/v2/pushes",
            headers={"Access-Token": token, "Content-Type": "application/json"},
            data=json.dumps({"type":"note","title": title,"body": body}, ensure_ascii=False).encode("utf-8"),
            timeout=20
        )
        ok = resp.status_code < 300
        return _result(ok, f"status={resp.status_code}")
    except Exception as e:
        return _result(False, f"exception: {e}")

# ---------------- Entry ----------------
def dispatch_report(pdf_path: str|Path, md_path: str|Path|None=None, title: str="VELOS 한국어 보고서") -> dict:
    pdf = Path(pdf_path)
    md  = Path(md_path) if md_path else None
    pdf.exists() or (_ for _ in ()).throw(FileNotFoundError(pdf))

    text = f"{title}\n파일: {pdf.name}"
    results = {
        "slack":   send_slack(pdf, text),
        "notion":  send_notion(pdf, md, title),
        "email":   send_email(pdf, subject=title, body=text),
        "push":    send_pushbullet(title, text),
        "channel": SLACK_CHANNEL_ID or "N/A",
        "database": _env("NOTION_DATABASE_ID") or "N/A",
        "file": str(pdf),
    }

    out = DISP / f"dispatch_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results

if __name__ == "__main__":
    # 수동 테스트용
    latest = max(AUTO.glob("velos_auto_report_*_ko.pdf"), default=None)
    md = max(AUTO.glob("velos_auto_report_*.md"), default=None)
    if latest:
        print(json.dumps(dispatch_report(latest, md), ensure_ascii=False, indent=2))
    else:
        print("no pdf found in", AUTO)

