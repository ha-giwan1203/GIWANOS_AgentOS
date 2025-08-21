# [ACTIVE] VELOS 이메일 전송 시스템 - 이메일 발송 스크립트
# -*- coding: utf-8 -*-
"""
VELOS 이메일 전송 스크립트
- PDF 파일 첨부 지원
- 환경변수 기반 유연한 설정
- SMTP 인증 및 TLS 지원
"""

import json
import mimetypes
import os
import smtplib
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# 환경변수 로딩
try:
    from env_loader import load_env

    load_env()
except ImportError:
    print("⚠️  env_loader 모듈을 찾을 수 없습니다", file=sys.stderr)
    sys.exit(1)


def attach_file(msg, file_path):
    """파일을 이메일에 첨부"""
    try:
        # MIME 타입 추측
        ctype, encoding = mimetypes.guess_type(file_path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"

        maintype, subtype = ctype.split("/", 1)

        # 파일 읽기 및 첨부
        with open(file_path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())
            encoders.encode_base64(part)

        # 파일명 설정
        filename = os.path.basename(file_path)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')

        msg.attach(part)
        return True

    except Exception as e:
        print(f"⚠️  파일 첨부 실패: {e}")
        return False


def send_email(
    smtp_host, smtp_port, smtp_user, smtp_pass, to_email, subject, body, attachment_path=None
):
    """이메일 전송"""
    try:
        # 이메일 메시지 구성
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email

        # 본문 추가
        msg.attach(MIMEText(body, _charset="utf-8"))

        # 첨부파일 추가
        attachment_success = False
        if attachment_path and os.path.exists(attachment_path):
            attachment_success = attach_file(msg, attachment_path)

        # SMTP 연결 및 전송
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())

        return {
            "ok": True,
            "attachment_included": attachment_success,
            "attachment_path": attachment_path if attachment_success else None,
        }

    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "error": "SMTP 인증 실패"}
    except smtplib.SMTPException as e:
        return {"ok": False, "error": f"SMTP 오류: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"전송 오류: {e}"}


def main():
    """메인 실행 함수"""
    print("📧 VELOS 이메일 전송 시작")
    print("=" * 40)

    # SMTP 설정
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    # 필수 환경변수 검증
    if not all([smtp_host, smtp_user, smtp_pass]):
        print("❌ SMTP 환경변수가 부족합니다:", file=sys.stderr)
        print(f"   SMTP_HOST: {'✅' if smtp_host else '❌'}", file=sys.stderr)
        print(f"   SMTP_USER: {'✅' if smtp_user else '❌'}", file=sys.stderr)
        print(f"   SMTP_PASS: {'✅' if smtp_pass else '❌'}", file=sys.stderr)
        sys.exit(2)

    # 이메일 내용 설정
    to_email = os.getenv("EMAIL_TO") or smtp_user
    subject = os.getenv("EMAIL_SUBJECT", "VELOS 보고서")
    body = os.getenv("EMAIL_BODY", "VELOS 자동 생성 보고서입니다.")
    pdf_path = os.getenv("VELOS_PDF_PATH", "")

    print("📝 이메일 정보:")
    print(f"   수신자: {to_email}")
    print(f"   제목: {subject}")
    print(f"   첨부파일: {pdf_path or '없음'}")
    print(f"   SMTP 서버: {smtp_host}:{smtp_port}")

    # 첨부파일 존재 확인
    if pdf_path and not os.path.exists(pdf_path):
        print(f"⚠️  첨부파일을 찾을 수 없습니다: {pdf_path}")
        pdf_path = None

    print(f"\n📤 이메일 전송 중...")

    # 이메일 전송
    result = send_email(
        smtp_host, smtp_port, smtp_user, smtp_pass, to_email, subject, body, pdf_path
    )

    if result.get("ok"):
        print("✅ 이메일 전송 성공!")
        if result.get("attachment_included"):
            print(f"   첨부파일: {os.path.basename(result.get('attachment_path'))}")

        # 성공 결과 JSON
        success_result = {
            "ok": True,
            "to": to_email,
            "subject": subject,
            "attachment_included": result.get("attachment_included"),
            "attachment_file": (
                os.path.basename(result.get("attachment_path"))
                if result.get("attachment_included")
                else None
            ),
        }

        print(json.dumps(success_result, ensure_ascii=False))
        return 0

    else:
        print("❌ 이메일 전송 실패:", file=sys.stderr)
        print(f"   오류: {result.get('error')}", file=sys.stderr)

        # 실패 결과 JSON
        error_result = {
            "ok": False,
            "error": result.get("error"),
            "to": to_email,
            "subject": subject,
        }

        print(json.dumps(error_result, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
