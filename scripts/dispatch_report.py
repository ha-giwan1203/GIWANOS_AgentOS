# [ACTIVE] scripts/dispatch_report.py
from __future__ import annotations
import os
import json
import time
import smtplib
import mimetypes
from pathlib import Path
from email.message import EmailMessage


# --- 환경변수 로딩 ---
def _load_dotenv():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    root = Path(r"C:\giwanos")
    for p in (root / "configs/.env", root / ".env"):
        if p.exists():
            load_dotenv(dotenv_path=p, override=True, encoding="utf-8")


_load_dotenv()

# 모듈 경로 수정
import sys
current_dir = Path.cwd()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    import requests  # venv에 이미 있을 가능성 높음
    from modules.utils.net import post_with_retry, get_with_retry
except Exception:
    requests = None  # 없으면 해당 채널은 자동 스킵
    post_with_retry = None
    get_with_retry = None

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

PUSHBULLET_TOKEN = _env("PUSHBULLET_TOKEN") or _env("PUSHBULLET_API_KEY")

SLACK_WEBHOOK_URL = _env("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN = _env("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = _env("SLACK_CHANNEL_ID") or _env("SLACK_CHANNEL")


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
                "attachments": [
                    {
                        "title": pdf_path.name,
                        "text": "VELOS 한국어 보고서가 생성되었습니다.",
                        "color": "good",
                    }
                ],
            }
            resp = (
                post_with_retry(webhook_url, json=payload, timeout=20, retries=2)
                if post_with_retry
                else requests.post(webhook_url, json=payload, timeout=20)
            )
            return _result(
                resp.status_code == 200, f"webhook: status={resp.status_code}"
            )
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
        resp = (
            post_with_retry(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                data={"channel": channel, "text": f"{text}\n파일 경로: {pdf_path}"},
                timeout=20,
                retries=2,
            )
            if post_with_retry
            else requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                data={"channel": channel, "text": f"{text}\n파일 경로: {pdf_path}"},
                timeout=20,
            )
        ).json()
        return _result(bool(resp.get("ok")), f"chat.postMessage: {resp}")
    except Exception as e:
        return _result(False, f"exception: {e}")


# ---------------- Notion ----------------
# 수정된 Notion 필드 매핑 정보:
# ==================================================
# 설명: summary (rich_text) - 안전값: 없음
# 날짜: created_at (date) - 안전값: 없음
# 상태: status (status) - 안전값: 보관, 진행 중, 업로드 완료
# 결과 ID: 결과_id (rich_text) - 안전값: 없음
# 장소: category (select) - 안전값: 모바일, 회사, 집
# 태그: tags (multi_select) - 안전값: 계약, 고객A, 예외
# 첨부파일: 첨부파일 (files) - 안전값: 없음
# 메타: 메타 (rich_text) - 안전값: 없음
# 경로: 경로 (rich_text) - 안전값: 없음
# 예측요약: 예측요약 (rich_text) - 안전값: 없음
# 작업: 작업 (rich_text) - 안전값: 없음
# 크기: 크기 (number) - 안전값: 없음
# 유형: type (select) - 안전값: 문서, 기타, 이미지
# 제목: title (title) - 안전값: 없음
# 설명: summary (rich_text)
# 날짜: created_at (date)
# 상태: 상태 (status)
# 결과 ID: content (rich_text)
# 장소: category (select)
# 태그: tags (multi_select)
# 첨부파일: 첨부파일 (files)
# 메타: content (rich_text)
# 경로: content (rich_text)
# 예측요약: content (rich_text)
# 작업: content (rich_text)
# 크기: version (number)
# 유형: category (select)
# 제목: title (title)
# 설명: summary (rich_text)
# 날짜: created_at (date)
# 상태: 상태 (status)
# 결과 ID: content (rich_text)
# 장소: category (select)
# 태그: tags (multi_select)
# 첨부파일: 첨부파일 (files)
# 메타: content (rich_text)
# 경로: content (rich_text)
# 예측요약: content (rich_text)
# 작업: content (rich_text)
# 크기: version (number)
# 유형: category (select)
# 제목: title (title)
def send_notion(pdf_path: Path, md_path: Path | None, title: str) -> dict:
    if not _env("DISPATCH_NOTION", "1") == "1":
        return _result(False, "disabled")
    token = _env("NOTION_TOKEN")
    database_id = _env("NOTION_DATABASE_ID")
    if not (token and database_id):
        return _result(False, "missing NOTION_TOKEN or NOTION_DATABASE_ID")
    if requests is None:
        return _result(False, "requests not installed")
    
    # 향상된 디스패치 방식 사용
    try:
        # 필드 매핑 로드 (수정된 버전 우선)
        mapping_file = Path("configs/notion_field_mapping_fixed.json")
        if not mapping_file.exists():
            mapping_file = Path("configs/notion_field_mapping.json")
        
        if not mapping_file.exists():
            return _result(False, "field mapping not found")
        
        import json
        mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
        
        # 보고서 데이터 준비
        from datetime import datetime
        report_data = {
            "title": title,
            "summary": f"VELOS 보고서: {pdf_path.name}",
            "created_at": datetime.now().isoformat(),
            "category": "VELOS_Report",
            "tags": ["VELOS", "자동생성"],
            "content": "",
            "file_url": str(pdf_path),
            "version": 1.0
        }
        
        # 마크다운 내용 추가
        if md_path and md_path.exists():
            try:
                md_content = md_path.read_text(encoding="utf-8", errors="ignore")
                report_data["content"] = md_content[:2000]  # Notion 제한
            except Exception:
                pass
        
        # Notion 속성 생성 (enhanced_dispatch 방식)
        properties = {}
        
        for field_name, field_config in mapping["fields"].items():
            notion_field = field_config["notion_field"]
            velos_field = field_config["velos_field"]
            field_type = field_config["type"]
            safe_values = field_config.get("safe_values", [])
            
            # VELOS 데이터에서 값 가져오기
            value = report_data.get(velos_field)
            if value is None:
                continue
            
            # 안전한 속성 생성
            try:
                if field_type == "title":
                    properties[notion_field] = {
                        "title": [{"text": {"content": str(value)}}]
                    }
                elif field_type == "rich_text":
                    properties[notion_field] = {
                        "rich_text": [{"text": {"content": str(value)}}]
                    }
                elif field_type == "date":
                    properties[notion_field] = {"date": {"start": str(value)}}
                elif field_type == "select":
                    if safe_values and str(value) in safe_values:
                        properties[notion_field] = {"select": {"name": str(value)}}
                    elif safe_values:
                        properties[notion_field] = {"select": {"name": safe_values[0]}}
                elif field_type == "multi_select":
                    if isinstance(value, list):
                        valid_values = [v for v in value if v in safe_values]
                        if valid_values:
                            properties[notion_field] = {
                                "multi_select": [{"name": v} for v in valid_values]
                            }
                    elif str(value) in safe_values:
                        properties[notion_field] = {
                            "multi_select": [{"name": str(value)}]
                        }
                elif field_type == "status":
                    if safe_values and str(value) in safe_values:
                        properties[notion_field] = {"status": {"name": str(value)}}
                    elif safe_values:
                        properties[notion_field] = {"status": {"name": safe_values[0]}}
                elif field_type == "number":
                    try:
                        properties[notion_field] = {"number": float(value)}
                    except (ValueError, TypeError):
                        continue
                elif field_type == "url":
                    properties[notion_field] = {"url": str(value)}
                
            except Exception:
                continue
        
        # 필수 필드 확인
        if "제목" not in properties:
            properties["제목"] = {"title": [{"text": {"content": title}}]}
        
        # API 요청
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=30
        )
        
        ok = resp.status_code < 300
        if ok:
            result = resp.json()
            page_id = result.get("id", "unknown")
            return _result(True, f"created page: {page_id}")
        else:
            return _result(False, f"status={resp.status_code}")
            
    except Exception as e:
        return _result(False, f"exception: {e}")


# ---------------- Email ----------------
def send_email(pdf_path: Path, subject: str, body: str) -> dict:
    if not _env("DISPATCH_EMAIL", "1") == "1":
        return _result(False, "disabled")
    host = SMTP_HOST
    port = int(SMTP_PORT)
    user = SMTP_USER
    pw = SMTP_PASS
    to = (_env("EMAIL_TO") or "").split(",")
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
        msg.add_attachment(
            pdf_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=pdf_path.name,
        )

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
        resp = (
            post_with_retry(
                "https://api.pushbullet.com/v2/pushes",
                headers={"Access-Token": token, "Content-Type": "application/json"},
                data=json.dumps(
                    {"type": "note", "title": title, "body": body}, ensure_ascii=False
                ).encode("utf-8"),
                timeout=20,
                retries=2,
            )
            if post_with_retry
            else requests.post(
                "https://api.pushbullet.com/v2/pushes",
                headers={"Access-Token": token, "Content-Type": "application/json"},
                data=json.dumps(
                    {"type": "note", "title": title, "body": body}, ensure_ascii=False
                ).encode("utf-8"),
                timeout=20,
            )
        )
        ok = resp.status_code < 300
        return _result(ok, f"status={resp.status_code}")
    except Exception as e:
        return _result(False, f"exception: {e}")


# ---------------- Entry ----------------
def dispatch_report(
    pdf_path: str | Path,
    md_path: str | Path | None = None,
    title: str = "VELOS 한국어 보고서",
) -> dict:
    pdf = Path(pdf_path)
    md = Path(md_path) if md_path else None
    pdf.exists() or (_ for _ in ()).throw(FileNotFoundError(pdf))

    text = f"{title}\n파일: {pdf.name}"
    results = {
        "slack": send_slack(pdf, text),
        "notion": send_notion(pdf, md, title),
        "email": send_email(pdf, subject=title, body=text),
        "push": send_pushbullet(title, text),
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
