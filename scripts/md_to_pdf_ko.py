# [ACTIVE] VELOS 마크다운 PDF 변환 시스템 - 한국어 PDF 생성 스크립트
from pathlib import Path
import sys, glob, datetime
import os

# ReportLab 기본 설치되어 있다고 가정 (없으면: pip install reportlab)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def find_korean_font() -> Path:
    """한글 폰트 파일을 찾습니다."""
    # 리눅스 호환 폰트 경로 candidates
    root = Path(os.getenv("VELOS_ROOT", "/workspace"))
    candidates = [
        root / "fonts" / "NanumGothic.ttf",
        root / "fonts" / "Nanum_Gothic" / "NanumGothic.ttf",
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),  # Ubuntu/Debian
        Path("/usr/share/fonts/TTF/NanumGothic.ttf"),  # Arch/CentOS
        Path("/System/Library/Fonts/AppleGothic.ttf"),  # macOS fallback
    ]
    for p in candidates:
        if p.exists():
            return p
    raise SystemExit("사용 가능한 한글 폰트 파일을 찾지 못했습니다. NanumGothic.ttf 설치 필요.")

def find_latest_md(dir_path: Path) -> Path:
    files = sorted(dir_path.glob("velos_auto_report_*.md"))
    if not files:
        raise SystemExit(f"리포트 .md 파일이 없습니다: {dir_path}")
    return files[-1]

def md_to_paragraphs(md_text: str):
    # 마크다운을 단순 파싱해서 Paragraph로 보냄(간소화: 헤더, 리스트, 일반 텍스트만)
    paras = []
    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line:
            paras.append(Spacer(1, 6))
            continue
        # 헤더 처리
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            size = {1:16, 2:14, 3:13}.get(level, 12)
            style = ParagraphStyle(name=f"h{level}", fontName="KFont", fontSize=size, leading=size+3, spaceAfter=6, spaceBefore=8, bold=True)
            paras.append(Paragraph(text, style))
            continue
        # 리스트 기호 처리
        if line.lstrip().startswith(("- ", "* ")):
            text = "• " + line.lstrip()[2:].strip()
        else:
            text = line
        body = ParagraphStyle(name="body", fontName="KFont", fontSize=11, leading=15)
        text = (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
        paras.append(Paragraph(text, body))
    return paras

def main():
    base = Path(r"C:\giwanos\data\reports\auto")
    target_md = None
    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".md"):
        target_md = Path(sys.argv[1])
    else:
        target_md = find_latest_md(base)

    if not target_md.exists():
        raise SystemExit(f"파일이 존재하지 않습니다: {target_md}")

    font_path = find_korean_font()
    pdfmetrics.registerFont(TTFont("KFont", str(font_path)))

    out_pdf = target_md.with_suffix(".pdf")
    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=42, bottomMargin=42)

    md_text = target_md.read_text(encoding="utf-8")
    story = md_to_paragraphs(md_text)
    doc.build(story)

    print(f"PDF OK -> {out_pdf}")

if __name__ == "__main__":
    main()



