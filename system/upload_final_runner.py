import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)


import os
import sys

# 루트 경로 등록
ROOT_DIR = "C:/giwanos"
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from upload_notion_safe import upload_to_notion

print("📤 전송기 시작")

# 회고 PDF 경로
reflection_pdf_path = os.path.join(ROOT_DIR, "reflections", "loop_reflection_log_clean.pdf")

# 메모 파일 경로
note_path = os.path.join(ROOT_DIR, "reflections", "loop_reflection_note.txt")

# PDF 존재하면 텍스트 파일로 메모 작성 후 업로드
if os.path.exists(reflection_pdf_path):
    print(f"📄 회고 PDF 발견: {reflection_pdf_path}")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(f"PDF 회고 파일 위치: {reflection_pdf_path}")
    upload_to_notion(note_path, page_title="GIWANOS 회고 요약 보고서")
else:
    print(f"❌ 회고 PDF 없음: {reflection_pdf_path}")

print("✅ 전송기 완료")
