#!/usr/bin/env python3
"""
VELOS Demo Integration Setup
데모용 외부 API 연동 설정 도구
"""

import os
import sys
from pathlib import Path

ROOT = Path("/home/user/webapp")

def setup_demo_env():
    """데모용 환경 변수 설정"""
    print("🚀 VELOS 데모 통합 연동 설정")
    print("=" * 50)
    
    # Create demo environment file
    env_file = ROOT / ".env"
    
    demo_env = """# VELOS Demo Integration Settings
# Notion Integration (데모용 - 실제 사용 시 실제 토큰으로 교체)
NOTION_TOKEN=demo_notion_token_for_testing
NOTION_DATABASE_ID=demo_database_id_12345
NOTION_RESULTID_PROP=결과 ID

# Slack Integration (데모용 - 실제 사용 시 실제 토큰으로 교체)
SLACK_BOT_TOKEN=xoxb-demo-slack-token-for-testing

# Email Notifications (옵션)
EMAIL_FROM=noreply@velos.local
EMAIL_TO=admin@velos.local

# PushBullet (옵션)
PUSHBULLET_TOKEN=demo_pushbullet_token
"""
    
    try:
        env_file.write_text(demo_env, encoding='utf-8')
        print(f"✅ 데모 환경 파일 생성: {env_file}")
        
        # Load environment variables
        for line in demo_env.split('\n'):
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
                print(f"   🔧 {key.strip()} = {value.strip()}")
        
        print("\n🎯 통합 연동 상태:")
        print(f"   📚 Notion: {'🟢 활성' if os.getenv('NOTION_TOKEN') else '🔴 비활성'}")
        print(f"   💬 Slack: {'🟢 활성' if os.getenv('SLACK_BOT_TOKEN') else '🔴 비활성'}")
        
        print("\n💡 참고:")
        print("   • 이는 데모용 설정입니다")
        print("   • 실제 사용 시 .env 파일의 토큰을 실제 값으로 교체하세요")
        print("   • 환경 변수는 streamlit 재시작 후 적용됩니다")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 실패: {str(e)}")
        return False

def load_env_file():
    """환경 파일 로드"""
    env_file = ROOT / ".env"
    if env_file.exists():
        try:
            content = env_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
            return True
        except Exception as e:
            print(f"환경 파일 로드 실패: {str(e)}")
            return False
    return False

if __name__ == "__main__":
    success = setup_demo_env()
    sys.exit(0 if success else 1)