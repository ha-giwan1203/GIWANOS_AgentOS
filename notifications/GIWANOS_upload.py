import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os

ROOT = "C:/giwanos"

print("📤 GIWANOS 전송 루프 실행 중...")

# 전송 대상 파일 목록 (예시: 회고 PDF, md, ZIP 백업)
targets = [
    os.path.join(ROOT, "reflections", "loop_reflection_log_clean.pdf"),
    os.path.join(ROOT, "reflections", "loop_reflection_log_20250719_214015.md"),
    max([os.path.join(ROOT, "loop_backups", f) for f in os.listdir(os.path.join(ROOT, "loop_backups")) if f.endswith(".zip")], key=os.path.getmtime)
]

# GitHub 업로드 대신 실제 전송 시뮬레이션
for f in targets:
    if os.path.exists(f):
        print(f"📎 전송 대상 확인됨: {f}")
        # 추후 GitHub API 또는 GDrive 전송 코드 삽입 위치
    else:
        print(f"⚠️ 전송 대상 파일 없음: {f}")

print("✅ 전송 루프 실행 완료 (실제 파일 기준 점검 완료)")
