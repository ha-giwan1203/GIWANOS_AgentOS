# -*- coding: utf-8 -*-
"""
VELOS 환경변수 로딩 모듈
- .env 파일 로딩
- 호환 매핑 처리
- 환경변수 검증
"""

import os
from pathlib import Path

def load_env():
    """환경변수 로딩 및 호환 매핑"""
    # .env 파일 로딩
    env_paths = [
        Path("C:/giwanos/configs/.env"),
        Path("C:/giwanos/.env"),
        Path(".env")
    ]

    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path=env_path, override=False, encoding="utf-8")
                print(f"✅ 환경변수 로드: {env_path}")
                loaded = True
                break
            except Exception as e:
                print(f"⚠️  환경변수 로드 실패: {env_path} - {e}")

    if not loaded:
        print("⚠️  .env 파일을 찾을 수 없습니다")

    # 호환 매핑 처리
    _apply_compatibility_mapping()

    return loaded

def _apply_compatibility_mapping():
    """환경변수 호환 매핑 적용"""
    # SMTP 호환 매핑
    os.environ.setdefault("SMTP_HOST", os.getenv("EMAIL_HOST", ""))
    os.environ.setdefault("SMTP_PORT", os.getenv("EMAIL_PORT", "587"))
    os.environ.setdefault("SMTP_USER", os.getenv("EMAIL_USER", ""))
    os.environ.setdefault("SMTP_PASS", os.getenv("EMAIL_PASSWORD", ""))

    # Pushbullet 호환 매핑
    if not os.getenv("PUSHBULLET_TOKEN") and os.getenv("PUSHBULLET_API_KEY"):
        os.environ["PUSHBULLET_TOKEN"] = os.getenv("PUSHBULLET_API_KEY")

    # Slack 호환 매핑
    if not os.getenv("SLACK_CHANNEL_ID") and os.getenv("SLACK_CHANNEL"):
        os.environ["SLACK_CHANNEL_ID"] = os.getenv("SLACK_CHANNEL")

def verify_env_vars():
    """필수 환경변수 검증"""
    required_vars = {
        "NOTION_TOKEN": "Notion API 토큰",
        "NOTION_DATABASE_ID": "Notion 데이터베이스 ID",
        "SLACK_WEBHOOK_URL": "Slack Webhook URL",
        "EMAIL_HOST": "이메일 SMTP 호스트",
        "EMAIL_USER": "이메일 사용자",
        "EMAIL_PASSWORD": "이메일 비밀번호",
        "PUSHBULLET_TOKEN": "Pushbullet API 토큰"
    }

    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")

    if missing:
        print("⚠️  누락된 환경변수:")
        for var in missing:
            print(f"   - {var}")
        return False

    print("✅ 모든 필수 환경변수가 설정되었습니다")
    return True

def get_env_summary():
    """환경변수 설정 요약"""
    summary = {
        "slack": {
            "webhook_url": bool(os.getenv("SLACK_WEBHOOK_URL")),
            "bot_token": bool(os.getenv("SLACK_BOT_TOKEN")),
            "channel_id": bool(os.getenv("SLACK_CHANNEL_ID"))
        },
        "email": {
            "host": bool(os.getenv("SMTP_HOST") or os.getenv("EMAIL_HOST")),
            "user": bool(os.getenv("SMTP_USER") or os.getenv("EMAIL_USER")),
            "password": bool(os.getenv("SMTP_PASS") or os.getenv("EMAIL_PASSWORD"))
        },
        "notion": {
            "token": bool(os.getenv("NOTION_TOKEN")),
            "database_id": bool(os.getenv("NOTION_DATABASE_ID"))
        },
        "pushbullet": {
            "token": bool(os.getenv("PUSHBULLET_TOKEN") or os.getenv("PUSHBULLET_API_KEY"))
        }
    }

    return summary

def print_env_status():
    """환경변수 상태 출력"""
    summary = get_env_summary()

    print("📊 환경변수 상태:")
    print("   📱 Slack:", "✅" if any(summary["slack"].values()) else "❌")
    print("   📧 Email:", "✅" if all(summary["email"].values()) else "❌")
    print("   📝 Notion:", "✅" if all(summary["notion"].values()) else "❌")
    print("   📱 Pushbullet:", "✅" if summary["pushbullet"]["token"] else "❌")

if __name__ == "__main__":
    # 테스트 실행
    print("🔧 VELOS 환경변수 로더 테스트")
    print("=" * 40)

    load_env()
    print_env_status()
    verify_env_vars()
