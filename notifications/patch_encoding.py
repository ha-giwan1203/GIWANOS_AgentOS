import os

# UTF-8 콘솔 재설정 헤더
HEADER = """import sys
import io

# 윈도우 콘솔을 UTF-8로 재설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""

# 패치할 파일 목록
FILES = ['memory_loader.py', 'memory_response_proxy.py']

def patch_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    if 'TextIOWrapper' in original:
        print(f"[SKIP] 이미 패치됨: {path}")
        return
    lines = original.splitlines(keepends=True)
    # 첫 줄이 셰뱅(#!)이면 그대로 두고 헤더 삽입
    if lines and lines[0].startswith('#!'):
        new_content = lines[0] + HEADER + ''.join(lines[1:])
    else:
        new_content = HEADER + original
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"[PATCHED] UTF-8 헤더 추가됨: {path}")

if __name__ == "__main__":
    cwd = os.getcwd()
    for fname in FILES:
        fullpath = os.path.join(cwd, fname)
        if os.path.exists(fullpath):
            patch_file(fullpath)
        else:
            print(f"[NOT FOUND] 파일 없음: {fullpath}")
