#!/usr/bin/env python
"""Streamlit VELOS Dashboard — Fixed
Notes:
- psutil.disk_usage() expects a *string* path, not pathlib.Path.
- Convert ROOT to str(ROOT) (e.g., 'C:\\giwanos') to avoid TypeError.
"""
import streamlit as st
import json, pathlib, datetime, psutil, platform, subprocess, time, sys

BASE_DIR = pathlib.Path(__file__).resolve().parent         # interface/
ROOT = BASE_DIR.parent                                     # C:\giwanos
REPORTS_DIR = ROOT / "data" / "reports"
MASTER_LOOP = ROOT / "scripts" / "run_giwanos_master_loop.py"

st.set_page_config(page_title="VELOS 대시보드", layout="wide")

# ───────────────────────────────── sidebar
with st.sidebar:
    st.title("📊 VELOS 요약")
    st.markdown(f"- OS : **{platform.system()} {platform.release()}**")
    st.markdown(f"- Python : **{platform.python_version()}**")
    st.markdown(f"- 실행 시각 : **{datetime.datetime.now():%Y-%m-%d %H:%M:%S}**")
    st.divider()

    if st.button("🛠 보고서 생성"):
        with st.spinner("Master Loop 실행 중…"):
            cmd = [sys.executable, str(MASTER_LOOP)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            st.text_area("Master Loop 출력", result.stdout + result.stderr, height=220)
            st.success("Master Loop 완료 — 새 보고서 확인 중")
            time.sleep(2)
            st.experimental_rerun()

# ───────────────────────────────── 시스템 실시간 상태
st.header("🖥️ 시스템 실시간 상태")
c1, c2, c3 = st.columns(3)
c1.metric("CPU 사용률", f"{psutil.cpu_percent():.1f} %")
c2.metric("메모리 사용률", f"{psutil.virtual_memory().percent:.1f} %")
# Convert ROOT to str to avoid TypeError on Windows
try:
    disk_percent = psutil.disk_usage(str(ROOT)).percent
except Exception:
    disk_percent = psutil.disk_usage('/').percent   # fallback
c3.metric("디스크 사용률", f"{disk_percent:.1f} %")

# ───────────────────────────────── 보고서 + 요약
st.header("📝 주간 보고서 및 요약")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
files = sorted(REPORTS_DIR.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]

# Auto-refresh
if files:
    newest_mtime = files[0].stat().st_mtime
    if "last_seen" not in st.session_state:
        st.session_state["last_seen"] = newest_mtime
    elif newest_mtime != st.session_state["last_seen"]:
        st.session_state["last_seen"] = newest_mtime
        st.experimental_rerun()

if not files:
    st.info("보고서가 아직 없습니다. 사이드바의 '보고서 생성' 버튼을 사용하세요.")
else:
    for f in files:
        if f.suffix == ".pdf":
            st.download_button(
                label=f"⬇️ {f.name}",
                data=f.read_bytes(),
                file_name=f.name,
                mime="application/pdf",
                key=f.name
            )
        elif f.suffix == ".summary.md":
            with st.expander(f"📝 요약 – {f.stem}"):
                st.markdown(f.read_text(encoding="utf-8"))
