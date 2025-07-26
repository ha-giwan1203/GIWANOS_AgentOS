#!/usr/bin/env python
import sys
import io
# 윈도우 콘솔을 UTF-8로 재설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import subprocess

BASE = os.getcwd()
errors = []

# 1) 필수 디렉터리 검사
print("🔍 1) 필수 디렉터리 검사")
required_dirs = [
    "__pycache__", "CoreState_Installed", "config", "logs",
    "loop_backups", "reflections", "reports", "scheduling",
    "snapshots"
]
for d in required_dirs:
    path = os.path.join(BASE, d)
    status = 'OK' if os.path.isdir(path) else 'MISSING'
    print(f"  - {d}: {status}")
    if status != 'OK':
        errors.append(f"Missing dir: {d}")

# 2) .py 파일 구문 검사
print("\n🔍 2) .py 파일 구문 검사")
for root, _, files in os.walk(BASE):
    for fn in files:
        if fn.endswith(".py"):
            full = os.path.join(root, fn)
            try:
                with open(full, 'r', encoding='utf-8') as sf:
                    compile(sf.read(), full, 'exec')
                print(f"  - {fn}: OK")
            except Exception as e:
                errors.append(f"Syntax error in {fn}: {e}")

# 3) 핵심 헬스 체크 스크립트 실행
print("\n🔍 3) 핵심 헬스 체크 스크립트 실행")
for script in ("memory_health_check_all.py", "memory_self_check.py"):
    if os.path.exists(script):
        try:
            out = subprocess.check_output(
                [sys.executable, script],
                stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace"
            )
            print(f"  - {script}: OK")
        except subprocess.CalledProcessError as e:
            errors.append(f"{script} failed: {e.output.strip()}")
    else:
        errors.append(f"{script} not found")

# 최종 요약
print("\n🚦 최종 요약")
if errors:
    print("❌ 다음 항목에서 문제가 발견되었습니다:")
    for e in errors:
        print("   -", e)
    sys.exit(1)
else:
    print("✅ 모든 검사가 정상적으로 통과했습니다.")