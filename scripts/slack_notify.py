# -*- coding: utf-8 -*-
"""
VELOS Slack 알림 스크립트
- 디스패치 완료 알림
- Notion 링크 포함
- 환경변수 기반 유연한 설정
"""

import os
import sys
import json
import requests
from pathlib import Path

# 환경변수 로딩
try:
    from env_loader import load_env
    load_env()
except ImportError:
    print("⚠️  env_loader 모듈을 찾을 수 없습니다", file=sys.stderr)
    sys.exit(1)


def send_slack_message(message, webhook_url):
    """Slack 메시지 전송"""
    try:
        response = requests.post(
            webhook_url,
            json={"text": message},
            timeout=10
        )

        if response.ok:
            return {"ok": True, "status_code": response.status_code}
        else:
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": response.text[:200]
            }

    except requests.exceptions.Timeout:
        return {"ok": False, "error": "타임아웃"}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e)}


def build_message(base_text, notion_url=None, additional_info=None):
    """Slack 메시지 구성"""
    message = base_text

    # Notion 링크 추가
    if notion_url:
        message += f"\n📝 Notion: {notion_url}"

    # 추가 정보 추가
    if additional_info:
        if isinstance(additional_info, dict):
            for key, value in additional_info.items():
                message += f"\n• {key}: {value}"
        else:
            message += f"\n{additional_info}"

    return message


def main():
    """메인 실행 함수"""
    print("📱 VELOS Slack 알림 시작")
    print("=" * 40)

    # 필수 환경변수 검증
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL이 설정되지 않았습니다", file=sys.stderr)
        sys.exit(2)

    # 메시지 구성
    base_text = os.getenv("SLACK_TEXT", "VELOS 디스패치 완료")
    notion_url = os.getenv("NOTION_PAGE_URL", "")
    additional_info = os.getenv("SLACK_ADDITIONAL_INFO", "")

    print("📝 알림 정보:")
    print(f"   기본 메시지: {base_text}")
    print(f"   Notion URL: {notion_url or '없음'}")
    print(f"   추가 정보: {additional_info or '없음'}")

    # 메시지 구성
    message = build_message(base_text, notion_url, additional_info)

    print(f"\n📤 Slack 메시지 전송 중...")
    print(f"   메시지 길이: {len(message)}자")

    # Slack 전송
    result = send_slack_message(message, webhook_url)

    if result.get("ok"):
        print("✅ Slack 알림 전송 성공!")
        print(f"   상태 코드: {result.get('status_code')}")

        # 성공 결과 JSON
        success_result = {
            "ok": True,
            "message_length": len(message),
            "notion_included": bool(notion_url),
            "status_code": result.get("status_code")
        }

        print(json.dumps(success_result, ensure_ascii=False))
        return 0

    else:
        print("❌ Slack 알림 전송 실패:", file=sys.stderr)
        print(f"   오류: {result.get('error')}", file=sys.stderr)
        if result.get("status_code"):
            print(f"   상태 코드: {result.get('status_code')}", file=sys.stderr)

        # 실패 결과 JSON
        error_result = {
            "ok": False,
            "error": result.get("error"),
            "status_code": result.get("status_code")
        }

        print(json.dumps(error_result, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
