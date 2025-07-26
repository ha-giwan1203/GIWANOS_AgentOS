import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
from dotenv import load_dotenv
from send_slack_report import send_slack_message
from upload_notion_safe import upload_to_notion

# .env 명시적 로딩
load_dotenv(dotenv_path="C:/giwanos/.env")

reflection_path = "C:/giwanos/reflections/loop_reflection_log.md"

print("📤 GIWANOS 회고 전송기 시작")

# 슬랙 전송
send_slack_message("✅ GIWANOS 자동 회고 전송 테스트")

# 노션 전송
if os.path.exists(reflection_path):
    print(f"📄 회고 파일 발견: {reflection_path}")
    upload_to_notion(reflection_path, page_title="GIWANOS 회고 리포트")
else:
    print(f"❌ 회고 파일 없음: {reflection_path}")

print("✅ 회고 전송 루프 종료")
