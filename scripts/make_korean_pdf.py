from pathlib import Path

from fpdf import FPDF

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "C:\giwanos"

    def get_data_path(*parts):
        return os.path.join("C:\giwanos", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("C:\giwanos", "configs", *parts)

    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"


FONT = Path("C:\giwanos/fonts/Nanum_Gothic/NanumGothic-Regular.ttf")
if not FONT.exists():
    raise SystemExit(f"폰트 파일 없음: {FONT}")

pdf = FPDF()
pdf.add_page()
pdf.add_font("Nanum", "", str(FONT), uni=True)
pdf.set_font("Nanum", size=12)
pdf.multi_cell(0, 8, "한글 보고서 정상 출력 확인\n줄바꿈도 OK")
out = Path(
    get_data_path("reports/test_korean.pdf")
    if "get_data_path" in locals()
    else "C:\giwanos/data/reports/test_korean.pdf"
)
pdf.output(str(out))
print("PDF OK ->", out)
