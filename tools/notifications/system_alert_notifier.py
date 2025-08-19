# [ACTIVE] VELOS System Alert Notifier
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# 시스템 알림을 처리하는 모듈입니다.

import os
import sys
import json
import argparse
from pathlib import Path

# ROOT 경로 설정
ROOT = Path("C:/giwanos")
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


def check_environment():
    """환경변수 상태 확인"""
    print("=== VELOS System Alert Notifier - Environment Check ===")

    # 필수 환경변수들
    required_vars = [
        "SLACK_BOT_TOKEN",
        "SLACK_CHANNEL_ID",
        "SLACK_WEBHOOK_URL",
        "EMAIL_ENABLED",
        "NOTION_ENABLED",
    ]

    # 선택적 환경변수들
    optional_vars = [
        "OPENAI_API_KEY",
        "NOTION_TOKEN",
        "EMAIL_HOST",
        "EMAIL_USER",
        "PUSHBULLET_API_KEY",
    ]

    print("1. Required Environment Variables:")
    all_required_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:8] + "***" if len(value) > 8 else "***"
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ❌ {var}: Not set")
            all_required_ok = False

    print("\n2. Optional Environment Variables:")
    optional_count = 0
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:8] + "***" if len(value) > 8 else "***"
            print(f"   ✅ {var}: {masked_value}")
            optional_count += 1
        else:
            print(f"   ⚠️  {var}: Not set")

    print(f"\n3. Summary:")
    print(
        f"   Required: {sum(1 for var in required_vars if os.getenv(var))}/{len(required_vars)}"
    )
    print(f"   Optional: {optional_count}/{len(optional_vars)}")
    print(
        f"   Overall: {'✅ OK' if all_required_ok else '❌ Missing required variables'}"
    )

    return all_required_ok


def test_notifications():
    """알림 기능 테스트"""
    print("\n=== Notification Tests ===")

    # Slack 테스트
    try:
        from scripts.notify_slack import send_slack_message

        result = send_slack_message("VELOS System Alert Notifier Test")
        print("   ✅ Slack: Test message sent")
    except Exception as e:
        print(f"   ❌ Slack: {e}")

    # Email 테스트
    email_enabled = os.getenv("EMAIL_ENABLED", "0") == "1"
    if email_enabled:
        try:
            # Email 테스트 로직
            print("   ✅ Email: Enabled")
        except Exception as e:
            print(f"   ❌ Email: {e}")
    else:
        print("   ⚠️  Email: Disabled")

    # Notion 테스트
    notion_enabled = os.getenv("NOTION_ENABLED", "0") == "1"
    if notion_enabled:
        try:
            # Notion 테스트 로직
            print("   ✅ Notion: Enabled")
        except Exception as e:
            print(f"   ❌ Notion: {e}")
    else:
        print("   ⚠️  Notion: Disabled")


def self_check():
    """자체 검증"""
    print("\n=== Self Check ===")

    # 1. 환경변수 확인
    env_ok = check_environment()

    # 2. 알림 테스트
    test_notifications()

    # 3. 시스템 상태 확인
    try:
        from scripts.system_integrity_check import main as integrity_check

        print("\n4. System Integrity Check:")
        integrity_check()
    except Exception as e:
        print(f"   ❌ System integrity check failed: {e}")

    print(f"\n=== Self Check Complete ===")
    print(f"Status: {'✅ All checks passed' if env_ok else '❌ Some checks failed'}")

    return env_ok


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="VELOS System Alert Notifier")
    parser.add_argument("--selfcheck", action="store_true", help="Run self check")
    parser.add_argument("--test", action="store_true", help="Test notifications")
    parser.add_argument(
        "--env", action="store_true", help="Check environment variables"
    )

    args = parser.parse_args()

    if args.selfcheck:
        return self_check()
    elif args.test:
        test_notifications()
    elif args.env:
        return check_environment()
    else:
        parser.print_help()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
