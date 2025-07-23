#!/usr/bin/env python
import os
import re
import io

# UTF-8 콘솔 재설정 헤더
UTF8_HEADER = (
    "import sys\n"
    "try:\n"
    "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
    "except AttributeError:\n"
    "    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)\n"
    "\n"
)

# 패치 대상 확장자
TARGET_EXT = '.py'

# 루트 디렉터리
ROOT = os.getcwd()

# 1) 모든 .py 파일에 UTF-8 헤더 추가
for dirpath, _, filenames in os.walk(ROOT):
    for fname in filenames:
        if not fname.endswith(TARGET_EXT):
            continue
        if fname in ['batch_patch_all_utf8.py', 'batch_update_giwanos.py']:
            continue  # 자기 자신 제외
        full = os.path.join(dirpath, fname)
        with open(full, 'r', encoding='utf-8') as f:
            src = f.read()
        if 'sys.stdout.reconfigure' in src or 'TextIOWrapper' in src:
            continue  # 이미 패치됨
        # 셰뱅 처리
        lines = src.splitlines(keepends=True)
        if lines and lines[0].startswith('#!'):
            new_src = lines[0] + UTF8_HEADER + ''.join(lines[1:])
        else:
            new_src = UTF8_HEADER + src
        with open(full, 'w', encoding='utf-8') as f:
            f.write(new_src)
        print(f"Patched UTF-8 header: {full}")

# 2) subprocess.check_output 호출 패치
pattern = re.compile(r"subprocess\.check_output\((\s*\[.*?\])(\s*,?)([^\)]*)\)", re.DOTALL)

for dirpath, _, filenames in os.walk(ROOT):
    for fname in filenames:
        if not fname.endswith(TARGET_EXT):
            continue
        if fname == 'batch_patch_all_utf8.py':
            continue
        full = os.path.join(dirpath, fname)
        with open(full, 'r', encoding='utf-8') as f:
            src = f.read()
        def repl(m):
            args, comma, opts = m.groups()
            # encoding, errors, text parameters
            new_opts = opts
            if 'encoding=' not in opts:
                if new_opts.strip() and not new_opts.strip().startswith('text='):
                    new_opts = ' text=True, encoding=\'utf-8\', errors=\'replace\',' + new_opts
                else:
                    new_opts = new_opts + ', encoding=\'utf-8\', errors=\'replace\''
            return f"subprocess.check_output({args}{comma}{new_opts})"
        new_src, count = pattern.subn(repl, src)
        if count:
            with open(full, 'w', encoding='utf-8') as f:
                f.write(new_src)
            print(f"Patched subprocess encoding in: {full} ({count} occurrences)")

print("Batch UTF-8 and encoding patches completed.")