# [ACTIVE] utils/net.py
import time
from typing import Any, Dict, Optional

import requests


def post_with_retry(url: str, **kw) -> requests.Response:
    """
    재시도 로직이 포함된 POST 요청

    Args:
        url: 요청할 URL
        **kw: requests.post에 전달할 키워드 인수들
            - timeout: 타임아웃 (기본값: 10초)
            - retries: 재시도 횟수 (기본값: 3회)
            - backoff: 백오프 배수 (기본값: 1.5)

    Returns:
        requests.Response: 성공한 응답

    Raises:
        Exception: 모든 재시도 실패 시 마지막 예외
    """
    timeout = kw.pop("timeout", 10)
    retries = kw.pop("retries", 3)
    backoff = kw.pop("backoff", 1.5)
    last = None

    for i in range(retries):
        try:
            return requests.post(url, timeout=timeout, **kw)
        except Exception as e:
            last = e
            if i < retries - 1:
                sleep_time = backoff**i
                time.sleep(sleep_time)

    raise last


def get_with_retry(url: str, **kw) -> requests.Response:
    """
    재시도 로직이 포함된 GET 요청

    Args:
        url: 요청할 URL
        **kw: requests.get에 전달할 키워드 인수들
            - timeout: 타임아웃 (기본값: 10초)
            - retries: 재시도 횟수 (기본값: 3회)
            - backoff: 백오프 배수 (기본값: 1.5)

    Returns:
        requests.Response: 성공한 응답

    Raises:
        Exception: 모든 재시도 실패 시 마지막 예외
    """
    timeout = kw.pop("timeout", 10)
    retries = kw.pop("retries", 3)
    backoff = kw.pop("backoff", 1.5)
    last = None

    for i in range(retries):
        try:
            return requests.get(url, timeout=timeout, **kw)
        except Exception as e:
            last = e
            if i < retries - 1:
                sleep_time = backoff**i
                time.sleep(sleep_time)

    raise last


def check_connectivity(urls: list = None) -> Dict[str, bool]:
    """
    여러 URL의 연결 상태를 확인

    Args:
        urls: 확인할 URL 리스트 (기본값: 일반적인 서비스들)

    Returns:
        Dict[str, bool]: URL별 연결 상태
    """
    if urls is None:
        urls = [
            "https://www.google.com",
            "https://api.pushbullet.com",
            "https://api.notion.com",
            "https://hooks.slack.com",
        ]

    results = {}

    for url in urls:
        try:
            response = get_with_retry(url, timeout=5, retries=1)
            results[url] = response.status_code < 400
        except Exception:
            results[url] = False

    return results


def test_velos_services() -> Dict[str, Any]:
    """
    VELOS 관련 서비스들의 연결 상태를 테스트

    Returns:
        Dict[str, Any]: 서비스별 테스트 결과
    """
    import os

    results = {
        "slack": {"status": "unknown", "detail": ""},
        "email": {"status": "unknown", "detail": ""},
        "pushbullet": {"status": "unknown", "detail": ""},
        "notion": {"status": "unknown", "detail": ""},
    }

    # Slack 테스트
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if webhook_url:
            response = post_with_retry(
                webhook_url, json={"text": "VELOS 연결 테스트"}, timeout=10, retries=2
            )
            results["slack"] = {
                "status": "success" if response.status_code == 200 else "failed",
                "detail": f"status={response.status_code}",
            }
        else:
            results["slack"] = {"status": "no_config", "detail": "SLACK_WEBHOOK_URL not set"}
    except Exception as e:
        results["slack"] = {"status": "error", "detail": str(e)}

    # Pushbullet 테스트
    try:
        token = os.getenv("PUSHBULLET_TOKEN") or os.getenv("PUSHBULLET_API_KEY")
        if token:
            response = post_with_retry(
                "https://api.pushbullet.com/v2/pushes",
                headers={"Access-Token": token, "Content-Type": "application/json"},
                json={"type": "note", "title": "VELOS Test", "body": "Connection test"},
                timeout=10,
                retries=2,
            )
            results["pushbullet"] = {
                "status": "success" if response.status_code < 300 else "failed",
                "detail": f"status={response.status_code}",
            }
        else:
            results["pushbullet"] = {"status": "no_config", "detail": "PUSHBULLET_TOKEN not set"}
    except Exception as e:
        results["pushbullet"] = {"status": "error", "detail": str(e)}

    # Notion 테스트
    try:
        token = os.getenv("NOTION_TOKEN")
        db_id = os.getenv("NOTION_DATABASE_ID")
        if token and db_id:
            response = get_with_retry(
                f"https://api.notion.com/v1/databases/{db_id}",
                headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
                timeout=10,
                retries=2,
            )
            results["notion"] = {
                "status": "success" if response.status_code == 200 else "failed",
                "detail": f"status={response.status_code}",
            }
        else:
            results["notion"] = {
                "status": "no_config",
                "detail": "NOTION_TOKEN or NOTION_DATABASE_ID not set",
            }
    except Exception as e:
        results["notion"] = {"status": "error", "detail": str(e)}

    # Email 테스트 (SMTP 연결만 확인)
    try:
        host = os.getenv("SMTP_HOST") or os.getenv("EMAIL_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        if host:
            import smtplib

            with smtplib.SMTP(host, port, timeout=10) as s:
                s.starttls()
                results["email"] = {"status": "success", "detail": "SMTP connection OK"}
        else:
            results["email"] = {"status": "no_config", "detail": "SMTP_HOST not set"}
    except Exception as e:
        results["email"] = {"status": "error", "detail": str(e)}

    return results


if __name__ == "__main__":
    # 테스트 실행
    print("🔍 VELOS 서비스 연결 테스트")
    print("=" * 50)

    results = test_velos_services()

    for service, result in results.items():
        status = result["status"]
        detail = result["detail"]

        if status == "success":
            print(f"✅ {service.upper()}: {detail}")
        elif status == "no_config":
            print(f"⚠️  {service.upper()}: {detail}")
        else:
            print(f"❌ {service.upper()}: {detail}")

    print("\n🌐 일반 연결 테스트")
    print("=" * 30)

    connectivity = check_connectivity()
    for url, is_connected in connectivity.items():
        status = "✅" if is_connected else "❌"
        print(f"{status} {url}")
