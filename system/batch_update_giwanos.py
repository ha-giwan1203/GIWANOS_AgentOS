#!/usr/bin/env python
import os
import subprocess
import sys

# 1) 기존 패치 스크립트 순차 실행
patch_scripts = [
    'patch_encoding.py',
    'patch_health_check.py',
    'patch_system_integrity.py'
]
for script in patch_scripts:
    if os.path.exists(script):
        print(f"Applying {script}...")
        subprocess.run([sys.executable, script], check=True)
    else:
        print(f"Skipping missing patch script: {script}")

# 2) loop_diagnostics.py 덮어쓰기
loop_diagnostics = """#!/usr/bin/env python
import sys
# 콘솔 출력을 UTF-8로 설정
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import json

def check_env(keys=["NOTION_TOKEN", "GITHUB_TOKEN"]):
    \"\"\"
    .env 파일을 읽어 Notion 및 GitHub 토큰 설정 여부를 확인합니다.
    \"\"\"
    results = {}
    if not os.path.exists(".env"):
        results[".env"] = "❌ 없음"
        return results
    with open(".env", "r", encoding="utf-8") as f:
        lines = f.readlines()
    env_dict = dict(line.strip().split("=", 1) for line in lines if "=" in line)
    for k in keys:
        results[k] = "✅ 설정됨" if env_dict.get(k) else "⚠️ 비어 있음"
    return results

def check_file_exists(files=["loop_memory_state.json", "loop_reflection_log.pdf"]):
    \"\"\"
    주요 결과 파일 존재 여부를 확인합니다.
    \"\"\"
    return {f: "✅ 있음" if os.path.exists(f) else "❌ 없음" for f in files}

def diagnose():
    print("🧠 GIWANOS 시스템 상태 진단")
    print("\\n📂 파일 상태:")
    for k, v in check_file_exists().items():
        print(f" • {k}: {v}")

    print("\\n🔑 환경 변수 상태:")
    for k, v in check_env().items():
        print(f" • {k}: {v}")

if __name__ == "__main__":
    diagnose()
"""
with open('loop_diagnostics.py', 'w', encoding='utf-8') as f:
    f.write(loop_diagnostics)
print("Updated loop_diagnostics.py")

# 3) memory_self_check.py 덮어쓰기
memory_self_check = """#!/usr/bin/env python
import sys
import io
# 윈도우 콘솔을 UTF-8로 재설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import json

def run_self_check():
    \"\"\"
    시스템의 메모리 구성요소 및 진단 로그 파일들이 모두 올바르게 존재하고 유효한지 검사합니다.
    \"\"\"
    errors = []
    base_dir = os.getcwd()

    # 검사 대상 파일 목록
    expected_files = [
        'memory_timeline.json',
        'restore_prompt.txt',
        'memory_loader.py',
        'install_memory_system.py',
        'memory_health_check_all.py',
        'memory_dashboard.md',
        'README.md',
        'memory_compressed.json',
        'memory_diagnosis_log.md'
    ]

    for fname in expected_files:
        fpath = os.path.join(base_dir, fname)
        if not os.path.exists(fpath):
            errors.append(f"Missing file: {fname}")

    # JSON 파일 유효성 검사
    for jfile in ['memory_timeline.json', 'memory_compressed.json']:
        jpath = os.path.join(base_dir, jfile)
        if os.path.exists(jpath):
            try:
                with open(jpath, 'r', encoding='utf-8') as jf:
                    json.load(jf)
            except Exception as e:
                errors.append(f"Invalid JSON in {jfile}: {e}")

    # 결과 출력
    if errors:
        print("🚨 Self-check detected issues:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)

if __name__ == "__main__":
    run_self_check()
    # SELF CHECK 완료 메시지 출력
    print("✅ memory_self_check.py: SELF CHECK OK")
"""
with open('memory_self_check.py', 'w', encoding='utf-8') as f:
    f.write(memory_self_check)
print("Updated memory_self_check.py")

print("All updates applied successfully.")