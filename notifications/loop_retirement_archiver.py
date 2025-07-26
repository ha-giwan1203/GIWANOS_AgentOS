import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
import os
import shutil

def archive_retired_loops():
    with open("loop_retirement_log.json", "r", encoding="utf-8") as f:
        retired = json.load(f)

    os.makedirs("archived_loops", exist_ok=True)
    for loop in retired:
        if os.path.exists(loop):
            shutil.move(loop, os.path.join("archived_loops", loop + ".old"))
            print(f"📦 보관됨: {loop}")

if __name__ == "__main__":
    archive_retired_loops()
