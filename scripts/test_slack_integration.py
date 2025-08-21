#!/usr/bin/env python3
# =========================================================
# VELOS Slack 통합 테스트 스크립트
# =========================================================

import os
import sys
import json
import time
from pathlib import Path

# 경로 추가
HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    env_file = ROOT / "configs" / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"✅ 환경 설정 로드: {env_file}")
    else:
        print(f"⚠️ 환경 설정 파일 없음: {env_file}")
except ImportError:
    print("⚠️ python-dotenv 설치 권장: pip install python-dotenv")

def check_environment():
    """환경 변수 확인"""
    print("\n🔍 환경 변수 확인:")
    
    required_vars = {
        "SLACK_BOT_TOKEN": "Slack Bot Token",
        "SLACK_CHANNEL_ID": "Slack Channel ID"
    }
    
    optional_vars = {
        "SLACK_WEBHOOK_URL": "Slack Webhook URL (선택사항)",
        "DISPATCH_SLACK": "Slack 전송 활성화",
        "NOTION_TOKEN": "Notion Token (선택사항)"
    }
    
    all_good = True
    
    for var, desc in required_vars.items():
        value = os.getenv(var, "").strip()
        if value and value != f"your-{var.lower().replace('_', '-')}-here":
            print(f"  ✅ {var}: {'*' * min(len(value), 20)}... ({desc})")
        else:
            print(f"  ❌ {var}: 미설정 ({desc})")
            all_good = False
    
    for var, desc in optional_vars.items():
        value = os.getenv(var, "").strip()
        if value and value != f"your-{var.lower().replace('_', '-')}-here":
            print(f"  ✅ {var}: {'*' * min(len(value), 15)}... ({desc})")
        else:
            print(f"  ⚪ {var}: 미설정 ({desc})")
    
    return all_good

def test_slack_api():
    """Slack API 연결 테스트"""
    print("\n🧪 Slack API 연결 테스트:")
    
    try:
        from scripts.notify_slack_api import SESSION, CHANNEL_ID
        
        # API 연결 테스트
        response = SESSION.post("https://slack.com/api/auth.test")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print(f"  ✅ API 연결 성공")
                print(f"  👤 사용자: {data.get('user', 'Unknown')}")
                print(f"  🏢 팀: {data.get('team', 'Unknown')}")
                print(f"  📍 채널 ID: {CHANNEL_ID}")
                return True
            else:
                print(f"  ❌ API 인증 실패: {data.get('error', 'Unknown')}")
                return False
        else:
            print(f"  ❌ HTTP 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ 예외 발생: {e}")
        return False

def test_message_send():
    """메시지 전송 테스트"""
    print("\n📨 메시지 전송 테스트:")
    
    try:
        from scripts.notify_slack_api import send_text, CHANNEL_ID
        
        test_message = f"🧪 VELOS 시스템 테스트 메시지 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        send_text(CHANNEL_ID, test_message)
        print(f"  ✅ 테스트 메시지 전송 완료")
        return True
        
    except Exception as e:
        print(f"  ❌ 메시지 전송 실패: {e}")
        return False

def test_dispatch_system():
    """Dispatch 시스템 테스트"""
    print("\n🌉 Bridge Dispatch 시스템 테스트:")
    
    try:
        # 테스트 메시지 큐 생성
        queue_dir = ROOT / "data" / "dispatch" / "_queue"
        queue_dir.mkdir(parents=True, exist_ok=True)
        
        test_message = {
            "title": "VELOS 시스템 테스트",
            "message": f"Bridge 시스템 연동 테스트 - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "channels": {
                "slack": {
                    "enabled": True,
                    "channel": os.getenv("SLACK_CHANNEL_ID", "#general")
                }
            }
        }
        
        # 테스트 파일 생성
        test_file = queue_dir / f"test_message_{int(time.time())}.json"
        test_file.write_text(json.dumps(test_message, ensure_ascii=False, indent=2), encoding="utf-8")
        
        print(f"  ✅ 테스트 메시지 큐 생성: {test_file.name}")
        
        # Bridge 시스템 실행
        from scripts.velos_bridge import main as bridge_main
        bridge_main()
        
        print(f"  ✅ Bridge 시스템 실행 완료")
        return True
        
    except Exception as e:
        print(f"  ❌ Dispatch 시스템 테스트 실패: {e}")
        return False

def check_processed_results():
    """처리 결과 확인"""
    print("\n📊 처리 결과 확인:")
    
    processed_dir = ROOT / "data" / "reports" / "_dispatch_processed"
    failed_dir = ROOT / "data" / "reports" / "_dispatch_failed"
    
    if processed_dir.exists():
        processed_files = list(processed_dir.glob("*.json"))
        print(f"  ✅ 성공 처리: {len(processed_files)}개 파일")
        
        if processed_files:
            latest = max(processed_files, key=lambda x: x.stat().st_mtime)
            try:
                data = json.loads(latest.read_text())
                status = "성공" if data.get("ok") else "실패"
                detail = data.get("detail", "N/A")
                print(f"  📄 최근 결과: {status} - {detail}")
            except:
                pass
    else:
        print(f"  ⚪ 성공 처리 디렉토리 없음")
    
    if failed_dir.exists():
        failed_files = list(failed_dir.glob("*.json"))
        print(f"  ⚠️ 실패 처리: {len(failed_files)}개 파일")
    else:
        print(f"  ✅ 실패 처리 디렉토리 없음")

def main():
    """메인 테스트 함수"""
    print("🚀 VELOS Slack 통합 기능 테스트 시작\n")
    print("=" * 50)
    
    # 1. 환경 변수 확인
    env_ok = check_environment()
    
    if not env_ok:
        print("\n❌ 필수 환경 변수가 설정되지 않았습니다.")
        print("📖 설정 가이드: /home/user/webapp/docs/SLACK_SETUP_GUIDE.md")
        return False
    
    # 2. API 연결 테스트
    api_ok = test_slack_api()
    
    if not api_ok:
        print("\n❌ Slack API 연결에 실패했습니다.")
        print("🔧 Bot Token과 권한을 확인해주세요.")
        return False
    
    # 3. 메시지 전송 테스트
    message_ok = test_message_send()
    
    # 4. Dispatch 시스템 테스트
    dispatch_ok = test_dispatch_system()
    
    # 5. 결과 확인
    check_processed_results()
    
    # 최종 결과
    print("\n" + "=" * 50)
    if all([env_ok, api_ok, message_ok, dispatch_ok]):
        print("🎉 모든 테스트 통과! Slack 통합 기능이 정상 작동합니다.")
        return True
    else:
        print("⚠️ 일부 테스트 실패. 설정을 확인해주세요.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)