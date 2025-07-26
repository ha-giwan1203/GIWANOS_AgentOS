import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import re

FILE = 'memory_health_check_all.py'
path = os.path.join(os.getcwd(), FILE)

# 파일 읽기
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# subprocess.check_output(...)에 encoding, errors 인자 삽입
pattern = r"(subprocess\.check_output\(\s*\[.*?\]\s*,\s*stderr=subprocess\.STDOUT)(\s*,\s*text=True)?\s*\)"
replacement = r"\1, text=True, encoding='utf-8', errors='replace')"

new_text, count = re.subn(pattern, replacement, text, flags=re.DOTALL)

if count == 0:
    print(f"[SKIP] 패치 대상 호출을 찾지 못했습니다: {FILE}")
else:
    # 덮어쓰기
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print(f"[PATCHED] UTF-8 디코딩 모드 적용: {FILE} ({count}곳 수정됨)")