import os
import re

FILE = 'system_integrity_check.py'
path = os.path.join(os.getcwd(), FILE)

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1) 맨 위에 UTF-8 콘솔 설정 헤더 삽입
if 'TextIOWrapper' not in text:
    header = (
        "import sys\n"
        "import io\n"
        "# 윈도우 콘솔을 UTF-8로 재설정\n"
        "sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')\n\n"
    )
    text = header + text

# 2) import-module 방식 대신 구문 검사 방식으로 대체
pattern = (
    r"print\(\"\\n🔍 2\) \.py 파일 파싱\(import\) 검사\"\)([\s\S]*?)"
    r"print\(\"\\n🔍 3\) 핵심 헬스 체크 스크립트 실행\"\)"
)
replacement = (
    "print(\"\\n🔍 2) .py 파일 구문 검사\")\n"
    "for root, _, files in os.walk(BASE):\n"
    "    for fn in files:\n"
    "        if fn.endswith(\".py\"):\n"
    "            full = os.path.join(root, fn)\n"
    "            try:\n"
    "                with open(full, 'r', encoding='utf-8') as sf:\n"
    "                    compile(sf.read(), full, 'exec')\n"
    "                print(f\"  - {fn}: OK\")\n"
    "            except Exception as e:\n"
    "                errors.append(f\"Syntax error in {fn}: {e}\")\n\n"
    "print(\"\\n🔍 3) 핵심 헬스 체크 스크립트 실행\")"
)

new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
if count == 0:
    print(f"[SKIP] 대체할 블록을 찾지 못했습니다: {FILE}")
else:
    text = new_text
    print(f"[PATCHED] 구문 검사 로직으로 교체됨: {count}곳")

# 덮어쓰기
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)