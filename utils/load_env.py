import os
from pathlib import Path

# 가상환경의 .env 파일 로드
venv_env_path = Path("C:/Users/User/venvs/velos/.env")

if venv_env_path.exists():
    print(f".env 파일 로드 중: {venv_env_path}")
    try:
        with open(venv_env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    print(f"로드됨: {key.strip()}")
        print("✅ .env 파일 로드 완료")
    except Exception as e:
        print(f"❌ .env 파일 로드 오류: {e}")
else:
    print(f"❌ .env 파일 없음: {venv_env_path}")

# 환경변수 확인
print("\n현재 환경변수 상태:")
print(f"SLACK_BOT_TOKEN: {'설정됨' if os.getenv('SLACK_BOT_TOKEN') else '없음'}")
print(f"SLACK_CHANNEL: {os.getenv('SLACK_CHANNEL', '없음')}")
print(f"SLACK_DEFAULT_CHANNEL: {os.getenv('SLACK_DEFAULT_CHANNEL', '없음')}")
print(f"SLACK_CHANNEL_ID: {os.getenv('SLACK_CHANNEL_ID', '없음')}")
