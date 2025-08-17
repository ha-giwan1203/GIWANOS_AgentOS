# -*- coding: utf-8 -*-
"""
VELOS 최종 완전 통합 워크플로우 스크립트
1. Notion DB 생성 (메타데이터 + REPORT_KEY)
2. Notion Page 생성 (Markdown 내용)
3. 이메일 전송 (PDF 첨부)
4. Slack 알림 (Notion 링크 포함)
5. Pushbullet 알림 (모바일 푸시)
"""

import os
import sys
import json
import subprocess
import datetime
import uuid
from pathlib import Path

# 환경변수 로딩
try:
    from env_loader import load_env
    load_env()
except ImportError:
    print("⚠️  env_loader 모듈을 찾을 수 없습니다", file=sys.stderr)
    sys.exit(1)


def generate_report_key():
    """고유한 REPORT_KEY 생성"""
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # UUID의 앞 8자리
    return f"{timestamp}_{unique_id}"


def run_script(script_name, env_vars=None):
    """Python 스크립트 실행"""
    cmd = [sys.executable, f"scripts/{script_name}"]

    # 환경변수 설정
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        if result.returncode == 0:
            # JSON 출력 파싱
            try:
                output_lines = result.stdout.strip().split('\n')
                json_line = output_lines[-1]  # 마지막 줄이 JSON
                return json.loads(json_line)
            except (json.JSONDecodeError, IndexError):
                return {"ok": True, "output": result.stdout}
        else:
            return {
                "ok": False,
                "error": result.stderr,
                "returncode": result.returncode
            }

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "타임아웃"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def find_latest_reports():
    """최신 보고서 파일 찾기"""
    auto_dir = Path(r"C:\giwanos\data\reports\auto")

    try:
        latest_pdf = max(auto_dir.glob("velos_auto_report_*_ko.pdf"))
        latest_md = max(auto_dir.glob("velos_auto_report_*.md"))
        return str(latest_pdf), str(latest_md)
    except ValueError:
        print("❌ 보고서 파일을 찾을 수 없습니다")
        return None, None


def main():
    """메인 워크플로우 함수"""
    print("🚀 VELOS 최종 완전 통합 워크플로우 시작")
    print("=" * 50)

    # REPORT_KEY 생성
    report_key = generate_report_key()
    print(f"📋 생성된 REPORT_KEY: {report_key}")

    # 최신 보고서 파일 찾기
    pdf_path, md_path = find_latest_reports()
    if not pdf_path or not md_path:
        return 1

    print(f"📄 처리할 파일:")
    print(f"   PDF: {Path(pdf_path).name}")
    print(f"   MD:  {Path(md_path).name}")

    # 1단계: Notion DB 생성 (REPORT_KEY 포함)
    print("\n🔹 1단계: Notion DB 생성")
    print("-" * 30)

    db_env = {
        "VELOS_TITLE": f"VELOS 보고서 - {Path(pdf_path).stem}",
        "VELOS_STATUS": "완료",
        "VELOS_TAGS": "자동화,보고서,VELOS",
        "REPORT_KEY": report_key
    }

    db_result = run_script("notion_db_create.py", db_env)

    if not db_result.get("ok"):
        print("❌ DB 생성 실패:")
        print(f"   오류: {db_result.get('error')}")
        return 1

    # 중복 실행 확인
    if db_result.get("status") == "이미 존재":
        print("⚠️  이미 존재하는 REPORT_KEY입니다!")
        print(f"   기존 페이지 ID: {db_result.get('page_id')}")
        print("   워크플로우를 중단합니다.")
        return 0

    print("✅ DB 생성 성공!")
    print(f"   페이지 ID: {db_result.get('page_id')}")
    print(f"   REPORT_KEY: {db_result.get('report_key')}")

    # 2단계: Notion Page 생성
    print("\n🔹 2단계: Notion Page 생성")
    print("-" * 30)

    page_env = {
        "VELOS_TITLE": f"VELOS 상세 보고서 - {Path(pdf_path).stem}",
        "VELOS_MD_PATH": md_path,
        "VELOS_PDF_PATH": pdf_path,
        "REPORT_KEY": report_key
    }

    page_result = run_script("notion_page_create.py", page_env)

    if not page_result.get("ok"):
        print("❌ Page 생성 실패:")
        print(f"   오류: {page_result.get('error')}")
        return 1

    print("✅ Page 생성 성공!")
    print(f"   페이지 ID: {page_result.get('page_id')}")
    print(f"   블록 수: {page_result.get('blocks_count')}개")
    print(f"   URL: {page_result.get('url')}")

    # 3단계: 이메일 전송
    print("\n🔹 3단계: 이메일 전송")
    print("-" * 20)

    email_env = {
        "EMAIL_SUBJECT": f"VELOS 보고서 - {Path(pdf_path).stem}",
        "EMAIL_BODY": f"VELOS 시스템에서 자동 생성된 보고서입니다.\n\nNotion 링크: {page_result.get('url')}\nREPORT_KEY: {report_key}",
        "VELOS_PDF_PATH": pdf_path
    }

    email_result = run_script("email_send.py", email_env)

    if not email_result.get("ok"):
        print("❌ 이메일 전송 실패:")
        print(f"   오류: {email_result.get('error')}")
        print("⚠️  이메일 전송 실패했지만 워크플로우는 계속 진행합니다")
    else:
        print("✅ 이메일 전송 성공!")
        print(f"   수신자: {email_result.get('to')}")
        if email_result.get("attachment_included"):
            print(f"   첨부파일: {email_result.get('attachment_file')}")

    # 4단계: Slack 알림
    print("\n🔹 4단계: Slack 알림")
    print("-" * 20)

    slack_env = {
        "SLACK_TEXT": f"VELOS 보고서 생성 완료! 📊",
        "NOTION_PAGE_URL": page_result.get("url"),
        "SLACK_ADDITIONAL_INFO": f"블록 수: {page_result.get('blocks_count')}개, 파일: {Path(pdf_path).name}, REPORT_KEY: {report_key}"
    }

    slack_result = run_script("slack_notify.py", slack_env)

    if not slack_result.get("ok"):
        print("❌ Slack 알림 실패:")
        print(f"   오류: {slack_result.get('error')}")
        print("⚠️  Slack 알림 실패했지만 워크플로우는 계속 진행합니다")
    else:
        print("✅ Slack 알림 성공!")
        print(f"   메시지 길이: {slack_result.get('message_length')}자")

    # 5단계: Pushbullet 알림
    print("\n🔹 5단계: Pushbullet 알림")
    print("-" * 20)

    pushbullet_env = {
        "PB_TITLE": f"VELOS 보고서 완료",
        "PB_BODY": f"보고서 생성이 완료되었습니다.\n\n파일: {Path(pdf_path).name}\nNotion: {page_result.get('url')}\nREPORT_KEY: {report_key}"
    }

    pushbullet_result = run_script("pushbullet_send.py", pushbullet_env)

    if not pushbullet_result.get("ok"):
        print("❌ Pushbullet 알림 실패:")
        print(f"   오류: {pushbullet_result.get('error')}")
        print("⚠️  Pushbullet 알림 실패했지만 워크플로우는 완료되었습니다")
    else:
        print("✅ Pushbullet 알림 성공!")
        print(f"   상태 코드: {pushbullet_result.get('status_code')}")

    # 최종 결과
    print("\n🎉 VELOS 최종 완전 통합 워크플로우 완료!")
    print("=" * 50)
    print("📊 생성된 항목들:")
    print(f"   📋 DB 항목: {db_result.get('page_id')}")
    print(f"   📄 상세 페이지: {page_result.get('url')}")
    print(f"   📧 이메일: {'성공' if email_result.get('ok') else '실패'}")
    print(f"   📱 Slack: {'성공' if slack_result.get('ok') else '실패'}")
    print(f"   📱 Pushbullet: {'성공' if pushbullet_result.get('ok') else '실패'}")
    print(f"   🔑 REPORT_KEY: {report_key}")

    # 통합 결과 JSON
    final_result = {
        "ok": True,
        "workflow_type": "velos_ultimate_complete",
        "report_key": report_key,
        "files": {
            "pdf": str(pdf_path),
            "md": str(md_path)
        },
        "results": {
            "database": db_result,
            "page": page_result,
            "email": email_result,
            "slack": slack_result,
            "pushbullet": pushbullet_result
        }
    }

    print(f"\n📋 워크플로우 결과 JSON:")
    print(json.dumps(final_result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
