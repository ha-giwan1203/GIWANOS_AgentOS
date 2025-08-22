#!/usr/bin/env python3
# =========================================================
# VELOS Slack 통합 빠른 설정 스크립트
# =========================================================

import os
import sys
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent

def create_directories():
    """필요한 디렉토리 생성"""
    print("📁 디렉토리 구조 생성 중...")
    
    directories = [
        "data/dispatch/_queue",
        "data/dispatch/_processed",
        "data/dispatch/_failed",
        "data/reports/_dispatch_processed", 
        "data/reports/_dispatch_failed",
        "logs",
        "configs"
    ]
    
    for dir_path in directories:
        full_path = ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")

def interactive_setup():
    """대화형 설정"""
    print("\n🎯 VELOS Slack 통합 설정을 시작합니다!")
    print("=" * 50)
    
    config = {}
    
    # Slack Bot Token
    print("\n1️⃣ Slack Bot Token 입력")
    print("   - Slack API에서 'xoxb-'로 시작하는 Bot Token을 복사해주세요")
    print("   - 가이드: https://api.slack.com/apps → OAuth & Permissions")
    
    while True:
        token = input("   Slack Bot Token: ").strip()
        if token.startswith("xoxb-") and len(token) > 20:
            config["SLACK_BOT_TOKEN"] = token
            break
        elif token.lower() == "skip":
            print("   ⚠️ 건너뜀 - 나중에 수동 설정 필요")
            config["SLACK_BOT_TOKEN"] = "xoxb-your-bot-token-here"
            break
        else:
            print("   ❌ 올바른 Bot Token을 입력해주세요 (또는 'skip' 입력)")
    
    # Slack Channel ID
    print("\n2️⃣ Slack Channel ID 입력")
    print("   - 메시지를 받을 채널의 ID를 입력해주세요")
    print("   - 형식: C1234567890 (채널) 또는 U1234567890 (사용자 DM)")
    
    while True:
        channel = input("   Channel ID: ").strip()
        if channel.startswith(("C", "G", "D", "U")) and len(channel) >= 10:
            config["SLACK_CHANNEL_ID"] = channel
            break
        elif channel.lower() == "skip":
            print("   ⚠️ 건너뜀 - 나중에 수동 설정 필요")
            config["SLACK_CHANNEL_ID"] = "C1234567890"
            break
        else:
            print("   ❌ 올바른 Channel ID를 입력해주세요 (또는 'skip' 입력)")
    
    # 추가 설정들
    config.update({
        "SLACK_CHANNEL": config["SLACK_CHANNEL_ID"],
        "SLACK_SUMMARY_CH": config["SLACK_CHANNEL_ID"], 
        "DISPATCH_SLACK": "1",
        "MEMORY_ENABLED": "1",
        "BRIDGE_ENABLED": "1",
        "DEBUG": "0",
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "/home/user/webapp/logs/velos.log"
    })
    
    return config

def save_env_file(config):
    """환경 파일 저장"""
    env_file = ROOT / "configs" / ".env"
    
    print(f"\n💾 환경 설정 파일 저장: {env_file}")
    
    env_content = """# =========================================================
# VELOS 환경 설정 파일 (자동 생성)
# Slack 통합전송 기능 설정
# =========================================================

# =========================
# SLACK 통합 설정
# =========================
"""
    
    for key, value in config.items():
        env_content += f"{key}={value}\n"
    
    env_content += """
# =========================
# 추가 통합 서비스 (선택사항)
# =========================
# NOTION_TOKEN=secret_your-notion-token-here
# OPENAI_API_KEY=sk-your-openai-api-key-here

# =========================
# 고급 설정
# =========================
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
"""
    
    env_file.write_text(env_content, encoding="utf-8")
    print("  ✅ 환경 설정 파일 저장 완료")

def create_test_message():
    """테스트 메시지 생성"""
    print("\n📨 테스트 메시지 생성 중...")
    
    queue_dir = ROOT / "data" / "dispatch" / "_queue"
    
    test_message = {
        "title": "🚀 VELOS 시스템 설정 완료",
        "message": "Slack 통합 기능이 성공적으로 설정되었습니다!\n\n✅ 환경 변수 구성\n✅ 디렉토리 생성\n✅ 테스트 메시지 생성\n\n이제 VELOS의 모든 알림과 보고서가 Slack으로 전송됩니다.",
        "channels": {
            "slack": {
                "enabled": True,
                "channel": "#general"
            }
        }
    }
    
    test_file = queue_dir / "setup_complete.json"
    test_file.write_text(json.dumps(test_message, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ 테스트 메시지 생성: {test_file.name}")

def show_next_steps():
    """다음 단계 안내"""
    print("\n🎉 VELOS Slack 통합 설정 완료!")
    print("=" * 50)
    
    print("\n📋 다음 단계:")
    print("1️⃣ Slack App에서 봇을 채널에 초대:")
    print("   - 채널에서 '/invite @your-bot-name' 실행")
    
    print("\n2️⃣ 통합 기능 테스트:")
    print("   cd /home/user/webapp")
    print("   python scripts/test_slack_integration.py")
    
    print("\n3️⃣ 수동으로 메시지 전송 테스트:")
    print("   python scripts/velos_bridge.py")
    
    print("\n4️⃣ 자동 보고서 업로드 테스트:")
    print("   python scripts/notify_slack_api.py")
    
    print("\n📖 도움말:")
    print("   - 설정 가이드: /home/user/webapp/docs/SLACK_SETUP_GUIDE.md")
    print("   - 환경 설정: /home/user/webapp/configs/.env")
    print("   - 로그 파일: /home/user/webapp/logs/velos_bridge.log")

def main():
    """메인 설정 함수"""
    print("🚀 VELOS Slack 통합 빠른 설정")
    print("=" * 40)
    
    try:
        # 1. 디렉토리 생성
        create_directories()
        
        # 2. 대화형 설정
        config = interactive_setup()
        
        # 3. 환경 파일 저장
        save_env_file(config)
        
        # 4. 테스트 메시지 생성
        create_test_message()
        
        # 5. 다음 단계 안내
        show_next_steps()
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 설정이 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n❌ 설정 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)