# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

import os
import sys

# UTF-8 인코딩 강제 설정
try:
    from utils.utf8_force import setup_utf8_environment
    setup_utf8_environment()
except ImportError:
    # utils 모듈을 찾을 수 없는 경우 직접 설정
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# VELOS 환경 변수 목록
velos_vars = [
    "VELOS_ROOT",
    "VELOS_DB",
    "VELOS_MEM_FAST",
    "VELOS_LOG_DIR",
    "VELOS_REPORT_DIR",
    "VELOS_SNAPSHOT_DIR",
    "VELOS_MEMORY_ONLY"
]

print("=== VELOS Environment Variables ===")
print("=" * 40)

for var in velos_vars:
    value = os.environ.get(var, "NOT_SET")
    print(f"{var}={value}")

print("\n=== Verification ===")
print("=" * 20)

# 기본값 확인
root = os.environ.get("VELOS_ROOT", "C:\\giwanos")
print(f"VELOS_ROOT exists: {os.path.exists(root)}")
print(f"VELOS_ROOT is dir: {os.path.isdir(root)}")

# 하위 디렉토리 확인
subdirs = ["data", "scripts", "modules", "interface"]
for subdir in subdirs:
    path = os.path.join(root, subdir)
    exists = os.path.exists(path)
    is_dir = os.path.isdir(path) if exists else False
    print(f"  {subdir}/: exists={exists}, is_dir={is_dir}")

print("\n[DONE] Environment check completed!")
