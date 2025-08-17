import os

print("=== .env 파일 내용 확인 ===")

try:
    with open('configs/.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"총 {len(lines)}줄")

    # 전송 관련 환경변수만 필터링
    transport_vars = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if any(keyword in line for keyword in ['SLACK_', 'NOTION_', 'EMAIL_', 'PUSHBULLET_']):
                transport_vars.append(line)

    print(f"\n전송 관련 환경변수 ({len(transport_vars)}개):")
    for var in transport_vars:
        print(f"  {var}")

    if not transport_vars:
        print("  전송 관련 환경변수가 없습니다.")

except FileNotFoundError:
    print("configs/.env 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"파일 읽기 오류: {e}")

print("\n=== 현재 환경변수와 비교 ===")
current_vars = ['SLACK_BOT_TOKEN', 'SLACK_CHANNEL', 'SLACK_CHANNEL_ID', 'NOTION_TOKEN', 'NOTION_DATABASE_ID', 'EMAIL_PASSWORD']
for var in current_vars:
    value = os.getenv(var)
    if value:
        print(f"  {var}: {'*' * len(value)}" if 'PASSWORD' in var or 'TOKEN' in var else f"  {var}: {value}")
    else:
        print(f"  {var}: 없음")
