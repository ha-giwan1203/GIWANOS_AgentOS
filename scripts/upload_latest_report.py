# 최신 보고서 별칭 생성 + Slack 업로드 실행기
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

from modules.report_paths import LATEST_PATH, REPORT_DIR, ROOT, latest_timestamped

ENV = ROOT / "configs" / ".env"
if not ENV.exists():
    print(f"[ERROR] .env 없음: {ENV}")
    sys.exit(1)
load_dotenv(dotenv_path=ENV)


def make_latest_alias(src: Path) -> Path:
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, LATEST_PATH)
        return LATEST_PATH
    except Exception as e:
        print(f"[ERROR] latest 별칭 생성 실패: {e}")
        return src  # 최소한 원본 업로드


if __name__ == "__main__":
    src = latest_timestamped()
    if not src:
        print("[WARN] 업로드할 보고서 없음")
        sys.exit(0)
    alias = make_latest_alias(src)
    print(f"[INFO] 업로드 대상: {alias} (원본: {src.name})")
    from scripts.notify_slack_api import send_report

    ok = send_report(alias, title=f"VELOS Report - {alias.name}")
    sys.exit(0 if ok else 1)
