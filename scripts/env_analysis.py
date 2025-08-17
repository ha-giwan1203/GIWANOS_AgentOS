import os
import sys
from pathlib import Path

print("=== 환경변수 원인 분석 ===")

# 1. 현재 환경변수 상태
print("1. 현재 환경변수 상태:")
env_vars = ['SLACK_BOT_TOKEN', 'SLACK_CHANNEL', 'SLACK_CHANNEL_ID', 'NOTION_TOKEN', 'NOTION_DATABASE_ID', 'EMAIL_PASSWORD']
for var in env_vars:
    value = os.getenv(var)
    if value:
        masked = '*' * len(value) if 'TOKEN' in var or 'PASSWORD' in var else value
        print(f"   {var}: {masked}")
    else:
        print(f"   {var}: 없음")

# 2. .env 파일 분석
print("\n2. .env 파일 분석:")
env_path = Path("configs/.env")
if env_path.exists():
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"   파일 크기: {len(lines)}줄")

        # 전송 관련 변수 찾기
        transport_vars = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if any(keyword in line for keyword in ['SLACK_', 'NOTION_', 'EMAIL_', 'PUSHBULLET_']):
                    transport_vars.append(line)

        print(f"   전송 관련 변수: {len(transport_vars)}개")
        for var in transport_vars:
            print(f"     {var}")

    except Exception as e:
        print(f"   파일 읽기 오류: {e}")
else:
    print("   .env 파일 없음")

# 3. 가상환경 확인
print("\n3. 가상환경 확인:")
venv_path = os.getenv('VIRTUAL_ENV')
if venv_path:
    print(f"   활성화된 가상환경: {venv_path}")

    # 가상환경의 .env 파일 확인
    venv_env = Path(venv_path) / '.env'
    if venv_env.exists():
        print(f"   가상환경 .env 파일: 있음 ({venv_env})")
    else:
        print(f"   가상환경 .env 파일: 없음")
else:
    print("   가상환경 미활성화")

# 4. 시스템 환경변수 확인
print("\n4. 시스템 환경변수 확인:")
system_vars = []
for var in env_vars:
    # 시스템 환경변수에서 확인 (가상환경 제외)
    if os.environ.get(var):
        system_vars.append(var)

if system_vars:
    print(f"   시스템에 설정된 변수: {', '.join(system_vars)}")
else:
    print("   시스템에 설정된 변수: 없음")

# 5. 원인 분석
print("\n5. 원인 분석:")
if any(os.getenv(var) for var in env_vars):
    print("   ✅ 환경변수는 정상적으로 설정되어 있음")
    print("   📝 누락된 변수들:")
    missing = [var for var in env_vars if not os.getenv(var)]
    for var in missing:
        print(f"     - {var}")
else:
    print("   ❌ 모든 환경변수가 누락됨")

print("\n=== 분석 완료 ===")
