
from dotenv import load_dotenv

from scripts.notify_slack_api import send_report

from modules.report_paths import ROOT
ENV = ROOT / "configs" / ".env"
if not ENV.exists():
    print(f"[ERROR] .env 없음: {ENV}")
    raise SystemExit(1)
load_dotenv(dotenv_path=ENV)

p = ROOT / "data" / "reports" / "velos_report_latest.pdf"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_bytes(b"%PDF-1.4\n% VELOS DUMMY\n")  # 최소 PDF 시그니처
print("[INFO] 대상:", p)
ok = send_report(p, title=f"VELOS Report - {p.name}")
print("[RESULT]", "OK" if ok else "FAIL")

