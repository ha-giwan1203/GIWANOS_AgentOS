# -*- coding: utf-8 -*-
"""
VELOS Pushbullet 알림 스크립트
- 푸시 알림 전송
- 재시도 로직 포함
- 환경변수 기반 유연한 설정
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# 환경변수 로딩
try:
    from env_loader import load_env
    load_env()
except ImportError:
    print("⚠️  env_loader 모듈을 찾을 수 없습니다", file=sys.stderr)
    sys.exit(1)


def post_with_retry(url, headers, json_body, timeout=10, retries=3):
    """재시도 로직이 포함된 POST 요청"""
    last_error = None

    for i in range(retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=json_body,
                timeout=timeout
            )

            if response.ok:
                return response
            else:
                # HTTP 오류는 재시도하지 않음
                return response

        except requests.exceptions.Timeout:
            last_error = f"타임아웃 (시도 {i+1}/{retries})"
        except requests.exceptions.ConnectionError:
            last_error = f"연결 오류 (시도 {i+1}/{retries})"
        except Exception as e:
            last_error = f"예상치 못한 오류: {e} (시도 {i+1}/{retries})"

        # 마지막 시도가 아니면 대기 후 재시도
        if i < retries - 1:
            wait_time = 1.5 ** i
            print(f"   ⏳ 재시도 대기 중... ({wait_time:.1f}초)")
            time.sleep(wait_time)

    # 모든 재시도 실패
    raise Exception(f"모든 재시도 실패: {last_error}")


def send_pushbullet_notification(token, title, body, timeout=15, retries=3):
    """Pushbullet 알림 전송"""
    try:
        url = "https://api.pushbullet.com/v2/pushes"
        headers = {
            "Access-Token": token,
            "Content-Type": "application/json"
        }

        payload = {
            "type": "note",
            "title": title,
            "body": body
        }

        response = post_with_retry(url, headers, payload, timeout, retries)

        if response.ok:
            return {
                "ok": True,
                "status_code": response.status_code,
                "response": response.json() if response.content else None
            }
        else:
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": response.text[:200]
            }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def main():
    """메인 실행 함수"""
    print("📱 VELOS Pushbullet 알림 시작")
    print("=" * 40)

    # 필수 환경변수 검증
    token = os.getenv("PUSHBULLET_TOKEN")
    if not token:
        print("❌ PUSHBULLET_TOKEN이 설정되지 않았습니다", file=sys.stderr)
        sys.exit(2)

    # 알림 내용 설정
    title = os.getenv("PB_TITLE", "VELOS")
    body = os.getenv("PB_BODY", "디스패치 완료")

    print("📝 알림 정보:")
    print(f"   제목: {title}")
    print(f"   내용: {body}")
    print(f"   토큰: {token[:10]}...")

    print(f"\n📤 Pushbullet 알림 전송 중...")

    # Pushbullet 전송
    result = send_pushbullet_notification(token, title, body)

    if result.get("ok"):
        print("✅ Pushbullet 알림 전송 성공!")
        print(f"   상태 코드: {result.get('status_code')}")

        # 성공 결과 JSON
        success_result = {
            "ok": True,
            "title": title,
            "body": body,
            "status_code": result.get("status_code"),
            "response": result.get("response")
        }

        print(json.dumps(success_result, ensure_ascii=False))
        return 0

    else:
        print("❌ Pushbullet 알림 전송 실패:", file=sys.stderr)
        print(f"   오류: {result.get('error')}", file=sys.stderr)
        if result.get("status_code"):
            print(f"   상태 코드: {result.get('status_code')}", file=sys.stderr)

        # 실패 결과 JSON
        error_result = {
            "ok": False,
            "error": result.get("error"),
            "status_code": result.get("status_code"),
            "title": title,
            "body": body
        }

        print(json.dumps(error_result, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
