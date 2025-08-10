"""Auto Summary Agent - uses optimized OpenAI client to summarize reports."""
import pathlib, re
from modules.core.openai_client import optimized_call

try:
    from pdfminer.high_level import extract_text
except ImportError:
    extract_text = None  # Optional dependency

MODEL_COMPLEXITY = "low"

def extract_text_from_pdf(pdf_path: pathlib.Path) -> str:
    if extract_text:
        return extract_text(str(pdf_path))
    # Fallback placeholder
    return f"(PDF parsing not available. Please install pdfminer.six)\nFile: {pdf_path.name}"

def run(pdf_path: pathlib.Path) -> pathlib.Path:
    text = extract_text_from_pdf(pdf_path)[:12000]  # hard cap to stay within context
    prompt = f"다음 보고서를 10줄 이내 한국어로 요약:\n\n{text}"
    summary = optimized_call(prompt, complexity=MODEL_COMPLEXITY)
    out_path = pdf_path.with_suffix('.summary.md')
    out_path.write_text(summary, encoding='utf-8')
    return out_path


