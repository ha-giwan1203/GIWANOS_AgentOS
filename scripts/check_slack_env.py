import os

print("Slack 환경변수 확인:")
print(f"SLACK_BOT_TOKEN: {os.getenv('SLACK_BOT_TOKEN', '없음')[:20]}..." if os.getenv('SLACK_BOT_TOKEN') else "SLACK_BOT_TOKEN: 없음")
print(f"SLACK_CHANNEL: {os.getenv('SLACK_CHANNEL', '없음')}")
print(f"SLACK_DEFAULT_CHANNEL: {os.getenv('SLACK_DEFAULT_CHANNEL', '없음')}")
print(f"SLACK_CHANNEL_ID: {os.getenv('SLACK_CHANNEL_ID', '없음')}")

# 가상환경의 .env 파일에서 확인
venv_env_path = "C:/Users/User/venvs/velos/.env"
if os.path.exists(venv_env_path):
    print(f"\n가상환경 .env 파일 확인: {venv_env_path}")
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
    print(f"\n가상환경 .env 파일 없음: {venv_env_path}")
