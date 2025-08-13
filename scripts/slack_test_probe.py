import os
import sys

sys.path.append(os.path.abspath(r"C:\giwanos"))

from scripts.notify_slack_api import ROOT, send_report

p = ROOT / "data" / "reports" / "velos_report_latest.pdf"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_bytes(b"%PDF-1.4\n% VELOS DUMMY\n")
print("[INFO] 테스트 파일 생성 완료:", p)

ok = send_report(p, title=f"VELOS Dummy - {p.name}")
print("[RESULT]", "OK" if ok else "FAIL")
