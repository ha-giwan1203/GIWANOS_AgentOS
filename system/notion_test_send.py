import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os
from dotenv import load_dotenv
from upload_notion_safe import upload_to_notion

# .env 파일 로딩
load_dotenv()

# 테스트 실행
upload_to_notion("C:/giwanos/reflections/loop_reflection_log_clean.pdf", "GIWANOS 회고 PDF 전송 테스트")
