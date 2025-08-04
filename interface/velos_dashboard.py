#!/usr/bin/env python
"""Streamlit VELOS Dashboard (v2)
Improvements:
- Asynchronous master loop trigger with progress
- Report list filters to .pdf and .md
- Memory‑efficient download for PDF (no full read)
"""
import streamlit as st
import pathlib, datetime, psutil, platform, subprocess, time, sys, os

BASE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = BASE_DIR.parent
REPORTS_DIR = ROOT / "data" / "reports"
MASTER_LOOP = ROOT / "scripts" / "run_giwanos_master_loop.py"

st.set_page_config(page_title="VELOS Dashboard", layout="wide")

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 VELOS 요약")
    st.markdown(f"- OS : **{platform.system()} {platform.release()}**")
    st.markdown(f"- Python : **{platform.python_version()}**")
    st.markdown(f"- Now : **{datetime.datetime.now():%Y-%m-%d %H:%M:%S}**")
    st.divider()

    if st.button("🛠 Run Master Loop"):
        with st.spinner("Master Loop running…"):
            proc = subprocess.Popen([sys.executable, str(MASTER_LOOP)],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True)
            output_lines = []
            progress = st.progress(0)
            while proc.poll() is None:
                line = proc.stdout.readline()
                if line:
                    output_lines.append(line.rstrip())
                    if len(output_lines) % 5 == 0:
                        progress.progress(min(95, len(output_lines) // 2))
            progress.progress(100)
            st.text_area("Master Loop Output", "\n".join(output_lines), height=250)
            st.success("Done. Reloading reports…")
            time.sleep(1)
            st.experimental_rerun()

# ── System metrics ─────────────────────────────────────────────
st.header("🖥️ System Status")
c1, c2, c3 = st.columns(3)
c1.metric("CPU", f"{psutil.cpu_percent():.1f}%")
c2.metric("Memory", f"{psutil.virtual_memory().percent:.1f}%")
try:
    disk_pct = psutil.disk_usage(str(ROOT)).percent
except Exception:
    disk_pct = psutil.disk_usage('/').percent
c3.metric("Disk", f"{disk_pct:.1f}%")

# ── Reports ────────────────────────────────────────────────────
st.header("📑 Recent Reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# file filter
report_files = [p for p in REPORTS_DIR.iterdir() if p.suffix.lower() in {'.pdf', '.md'}]
files_sorted = sorted(report_files, key=lambda p: p.stat().st_mtime, reverse=True)[:20]

if not files_sorted:
    st.info("No reports yet. Use the sidebar button.")
else:
    for f in files_sorted:
        if f.suffix == '.pdf':
            with f.open('rb') as fp:
                st.download_button(f"⬇️ {f.name}", fp, file_name=f.name, mime="application/pdf", key=f.name)
        elif f.suffix == '.md':
            with st.expander(f"📝 {f.name}"):
                st.markdown(f.read_text(encoding='utf-8'))
