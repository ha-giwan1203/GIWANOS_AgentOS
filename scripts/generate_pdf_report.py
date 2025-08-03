"""VELOS PDF report + Slack (ISO‑8601·키 이름 호환 + Header Fix)"""

import pathlib, sys, datetime, json, warnings, importlib
import pandas as pd, matplotlib.pyplot as plt
from fpdf import FPDF

# ── 프로젝트 루트 추가 ────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
# ────────────────────────────────────────────────────

# 🔔 Slack 자동 탐지
smod = importlib.import_module("tools.notifications.slack_api")
slack_send = (
    getattr(smod, "send", None) or
    getattr(smod, "notify", None) or
    getattr(smod, "post_message", None) or
    (getattr(smod, "SlackNotifier")().push if hasattr(smod, "SlackNotifier")
     else lambda msg, *a, **k: print("SlackStub:", msg))
)

# 📁 경로
LOG  = ROOT / "data/logs/system_health.json"
DST  = ROOT / "data/reports"; DST.mkdir(parents=True, exist_ok=True)
FONTS = ROOT / "fonts"
FONT  = FONTS / "NotoSansKR-Regular.ttf"
FALL  = FONTS / "NanumGothic-Regular.ttf"
EMO   = FONTS / "NotoEmoji-Regular.ttf"

# ── 로드 함수 (필드·타임스탬프 호환) ─────────────────────
ALIAS = {
    "cpu_usage_percent":    "cpu_percent",
    "memory_usage_percent": "memory_percent",
    "disk_usage_percent":   "disk_percent",
}
def load(days: int = 7) -> pd.DataFrame:
    raw = json.loads(LOG.read_text(encoding="utf-8"))
    raw = [raw] if isinstance(raw, dict) else raw
    norm = []
    for r in raw:
        for old, new in ALIAS.items():
            if old in r and new not in r:
                r[new] = r.pop(old)
        norm.append(r)
    df = pd.DataFrame(norm)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=days)
    return df[df["timestamp"] >= cutoff]

def make_chart(df, col, path):
    plt.figure()
    df.plot(x="timestamp", y=col, title=f"{col} last 7d", legend=False)
    plt.ylabel("%")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

class PDF(FPDF): pass

def reg_fonts(pdf):
    for p in (FONT, FALL):
        if p.exists():
            pdf.add_font("Body", "", str(p), uni=True)
            pdf.add_font("Body", "B", str(p), uni=True)
            pdf.set_font("Body", "", 12)
            break
    if EMO.exists():
        try:
            pdf.add_font("NotoEmoji", "", str(EMO), uni=True)
        except Exception:
            pass

def generate() -> pathlib.Path:
    df = load()
    metrics = {"cpu_percent": "CPU", "memory_percent": "MEM", "disk_percent": "DISK"}
    tmp = pathlib.Path("tmp_charts"); tmp.mkdir(exist_ok=True)
    imgs = []
    for col, label in metrics.items():
        if col in df.columns:
            img = tmp / f"{col}.png"; make_chart(df, col, img); imgs.append(img)

    pdf = PDF(); reg_fonts(pdf)

    # ✅ Header 고정 (self 제대로 바인딩)
    def header(self):
        self.set_font("Body", "B", 16)
        self.cell(0, 10, "VELOS Weekly System Report", ln=True, align="C")
    pdf.header = header.__get__(pdf, PDF)

    pdf.add_page()
    pdf.set_font("Body", "", 12)
    pdf.cell(0, 8,
             f"Date Range: {df['timestamp'].min().date()} – {df['timestamp'].max().date()}",
             ln=True)
    pdf.ln(1)
    for col, label in metrics.items():
        if col in df.columns:
            pdf.cell(0, 8, f"{label} Avg: {df[col].mean():.2f}%", ln=True)
    pdf.ln(4)
    for img in imgs:
        pdf.image(str(img), w=180); pdf.ln(3)

    name = f"weekly_report_{datetime.date.today():%Y-%m-%d}.pdf"
    out = DST / name
    pdf.output(str(out))
    for img in imgs: img.unlink()
    tmp.rmdir()
    return out

if __name__ == "__main__":
    try:
        path = generate()
        print("Generated:", path)
        slack_send(f"📝 Report generated: {path.name}")
    except Exception as e:
        print("ERROR:", e)
        slack_send(f"❌ Report failed: {e}")
