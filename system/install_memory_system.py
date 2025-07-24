import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import shutil

files = [
    "memory_timeline.json",
    "memory_status.json",
    "restore_prompt.txt",
    "memory_log.md",
    "memory_updater.py",
    "memory_loader.py",
    "memory_guard.py",
    "memory_snapshot.py",
    "memory_filter.py",
    "memory_expiry_checker.py",
    "memory_analyzer.py",
    "memory_compressor.py",
    "memory_merger.py",
    "memory_cleaner.py",
    "memory_reasoner.py"
]

INSTALL_DIR = "CoreState_Installed"

if not os.path.exists(INSTALL_DIR):
    os.makedirs(INSTALL_DIR)

for f in files:
    if os.path.exists(f):
        shutil.copy(f, INSTALL_DIR)

print(f"✅ GIWANOS CoreState 설치 완료 → ./{INSTALL_DIR}")
