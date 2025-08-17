import os

print("현재 Slack 환경변수 상태:")
print(f"SLACK_BOT_TOKEN: {os.getenv('SLACK_BOT_TOKEN', '없음')}")
print(f"SLACK_CHANNEL: {os.getenv('SLACK_CHANNEL', '없음')}")
print(f"SLACK_DEFAULT_CHANNEL: {os.getenv('SLACK_DEFAULT_CHANNEL', '없음')}")
print(f"SLACK_CHANNEL_ID: {os.getenv('SLACK_CHANNEL_ID', '없음')}")

print("\n가상환경 .env 파일에서 로드되는지 확인:")
venv_env_path = "C:/Users/User/venvs/velos/.env"
if os.path.exists(venv_env_path):
    print(f"가상환경 .env 파일 존재: {venv_env_path}")
    try:
        with open(venv_env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('SLACK_BOT_TOKEN='):
                    token = line.strip().split('=', 1)[1]
                    print(f"가상환경 SLACK_BOT_TOKEN: {token[:20]}...")
                    break
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
else:
    print(f"가상환경 .env 파일 없음: {venv_env_path}")
