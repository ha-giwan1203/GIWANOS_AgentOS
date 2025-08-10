
# -*- coding: utf-8 -*-
"""
VELOS email sender
- 서로 다른 환경변수 키 이름을 모두 허용 (이식성 ↑)
- .env를 쓰면 자동 로드, 없으면 OS 환경변수 사용
- STARTTLS/SSL 모두 지원
- 첨부 파일 전송 지원
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

try:
    from dotenv import load_dotenv
    # CWD/.env, 프로젝트 루트(.env) 모두 시도
    load_dotenv(dotenv_path=os.getenv("DOTENV_PATH") or ".env")
except Exception:
    # python-dotenv 미설치 또는 기타 문제는 무시
    pass


def getenv_multi(*keys, default=None):
    """여러 키 중 먼저 발견되는 환경변수 값을 반환"""
    for k in keys:
        v = os.getenv(k)
        if v not in (None, ""):
            return v
    return default


def _smtp_connect(server, port, use_ssl=False):
    if use_ssl:
        return smtplib.SMTP_SSL(server, port)
    return smtplib.SMTP(server, port)


def _pick_bool(val, fallback=False):
    if val is None:
        return fallback
    return str(val).strip().lower() in ("1", "true", "yes", "y", "on")


def _resolve_email_config():
    """
    우선순위 규칙:
    - 발신자: EMAIL_FROM > EMAIL_USER > EMAIL_USERNAME
    - 비밀번호: EMAIL_PASS > EMAIL_PASSWORD > APP_PASSWORD
    - 수신자: EMAIL_TO > EMAIL_RECEIVER
    - 호스트/포트: EMAIL_HOST/EMAIL_PORT (기본: smtp.naver.com:587)
    - 보안: EMAIL_USE_SSL / EMAIL_USE_STARTTLS
    - 전체 on/off: EMAIL_ENABLED (기본 0=비활성)
    """
    enabled = _pick_bool(getenv_multi("EMAIL_ENABLED"), fallback=False)

    from_email = getenv_multi("EMAIL_FROM", "EMAIL_USER", "EMAIL_USERNAME")
    to_email   = getenv_multi("EMAIL_TO", "EMAIL_RECEIVER")
    password   = getenv_multi("EMAIL_PASS", "EMAIL_PASSWORD", "APP_PASSWORD")

    host = getenv_multi("EMAIL_HOST", default="smtp.naver.com")
    try:
        port = int(getenv_multi("EMAIL_PORT", default="587"))
    except ValueError:
        port = 587

    use_ssl      = _pick_bool(getenv_multi("EMAIL_USE_SSL"), fallback=False)
    use_starttls = _pick_bool(getenv_multi("EMAIL_USE_STARTTLS"), fallback=True if not use_ssl else False)

    return {
        "enabled": enabled,
        "from_email": from_email,
        "to_email": to_email,
        "password": password,
        "host": host,
        "port": port,
        "use_ssl": use_ssl,
        "use_starttls": use_starttls,
    }


def _send_message(msg, host, port, from_email, password, use_ssl=False, use_starttls=True):
    with _smtp_connect(host, port, use_ssl=use_ssl) as server:
        server.ehlo()
        if not use_ssl and use_starttls:
            server.starttls()
            server.ehlo()
        if from_email and password:
            server.login(from_email, password)
        server.send_message(msg)


def send_email_report(subject: str, body: str, to_email: str | None = None) -> bool:
    cfg = _resolve_email_config()
    if not cfg["enabled"]:
        print("✋ EMAIL_ENABLED=0 — 전송 건너뜀")
        return False

    from_email = cfg["from_email"]
    to_email = to_email or cfg["to_email"]
    password = cfg["password"]

    if not subject or not body:
        print("❌ 이메일 전송 실패: subject/body 누락")
        return False
    if not from_email:
        print("❌ 이메일 전송 실패: 발신자 이메일(EMAIL_FROM/EMAIL_USER)이 필요합니다")
        return False
    if not to_email:
        print("❌ 이메일 전송 실패: 수신자 이메일(EMAIL_TO/EMAIL_RECEIVER)이 필요합니다")

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        _send_message(
            msg=msg,
            host=cfg["host"],
            port=cfg["port"],
            from_email=from_email,
            password=password,
            use_ssl=cfg["use_ssl"],
            use_starttls=cfg["use_starttls"],
        )
        print("✅ 이메일 전송 성공")
        return True
    except Exception as e:
        print("❌ 이메일 전송 실패:", repr(e))
        return False


def send_report_email(pdf_path: str, subject: str = "📄 VELOS 주간 보고서", body: str | None = None) -> bool:
    cfg = _resolve_email_config()
    if not cfg["enabled"]:
        print("✋ EMAIL_ENABLED=0 — 전송 건너뜀")
        return False

    from_email = cfg["from_email"]
    to_email = cfg["to_email"]
    password = cfg["password"]

    if not from_email or not to_email:
        print("❌ 이메일 전송 실패: from/to 이메일 정보 부족")
        return False
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"❌ 첨부파일 없음: {pdf_path}")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        body_text = body or "VELOS 시스템에서 생성된 주간 보고서를 첨부드립니다."
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(pdf_path)
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)

        _send_message(
            msg=msg,
            host=cfg["host"],
            port=cfg["port"],
            from_email=from_email,
            password=password,
            use_ssl=cfg["use_ssl"],
            use_starttls=cfg["use_starttls"],
        )
        print("✅ 보고서 이메일 전송 완료")
        return True
    except Exception as e:
        print("❌ 보고서 이메일 전송 실패:", repr(e))
        return False


if __name__ == "__main__":
    # 간이 테스트: 본문 전송
    ok = send_email_report(
        subject="[VELOS] 테스트 메일",
        body="이메일 엔진 동작 테스트입니다.",
        to_email=getenv_multi("EMAIL_TO", "EMAIL_RECEIVER"),
    )
    print("send_email_report:", ok)
