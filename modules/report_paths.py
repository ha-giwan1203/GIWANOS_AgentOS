# report_paths.py — 보고서 경로/헬퍼 통일
import os
from pathlib import Path

ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos"))
REPORT_DIR = ROOT / "data" / "reports"
LATEST_NAME = "velos_report_latest.pdf"
LATEST_PATH = REPORT_DIR / LATEST_NAME


def latest_timestamped():
    if not REPORT_DIR.exists():
        return None
    files = sorted(
        REPORT_DIR.glob("velos_report_*.pdf"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None
