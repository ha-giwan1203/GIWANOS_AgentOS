import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import shutil

base = os.path.dirname(os.path.abspath(__file__))
candidate = os.path.join(base, "_정리_후보")
keep = os.path.join(base, "_보존")
review = os.path.join(base, "_검토_필요")
log = os.path.join(base, "trigger_execution.log")

os.makedirs(keep, exist_ok=True)
os.makedirs(review, exist_ok=True)

print("🧹 정리기 실행 시작")
with open(log, "a", encoding="utf-8") as f:
    f.write("🧹 정리기 실행 시작\n")

moved_to_keep = []
moved_to_review = []

for file in os.listdir(candidate):
    src = os.path.join(candidate, file)
    if file.endswith(".zip") or "보존" in file:
        shutil.move(src, os.path.join(keep, file))
        moved_to_keep.append(file)
    else:
        shutil.move(src, os.path.join(review, file))
        moved_to_review.append(file)

with open(log, "a", encoding="utf-8") as f:
    f.write("✅ 정리기 실행 완료\n")

print(f"📦 _보존 으로 이동된 파일: {moved_to_keep}")
print(f"🗂️ _검토_필요 로 이동된 파일: {moved_to_review}")
print("✅ 정리기 실행 완료")
