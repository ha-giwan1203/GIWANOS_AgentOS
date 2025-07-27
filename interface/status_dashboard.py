# C:/giwanos/interface/status_dashboard.py

import os
import psutil
import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import re
import warnings

# Suppress specific Streamlit warnings
warnings.filterwarnings(
    'ignore',
    'Thread.*missing ScriptRunContext.*',
    module='streamlit.runtime.scriptrunner_utils'
)

st.set_page_config(page_title="GIWANOS 시스템 상태 대시보드", layout="wide")
st.title("GIWANOS 시스템 상태 대시보드")

# System metrics
cpu_now = psutil.cpu_percent()
mem_now = psutil.virtual_memory().percent
disk_now = psutil.disk_usage("C:/giwanos").percent

# Display key metrics
cols = st.columns(5)
cols[0].metric("CPU Usage", f"{cpu_now:.1f}%")
cols[1].metric("Memory Usage", f"{mem_now:.1f}%")
cols[2].metric("Disk Usage", f"{disk_now:.1f}%")
cols[3].metric("Judgment Rules", 20)
cols[3].metric("Fallback Count", 19)
cols[3].metric("Fallback Rate", "95.0%")
reports_dir = "C:/giwanos/data/reports"
latest_reports = sorted(os.listdir(reports_dir)) if os.path.isdir(reports_dir) else []
cols[4].metric("Latest Report", latest_reports[-1] if latest_reports else "N/A")

st.markdown("---")

# Load and display master loop log
log_path = "C:/giwanos/data/logs/master_loop_execution.log"
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        full_log = f.read()

    st.subheader("Master Loop Log (Raw)")
    st.code(full_log, language="text")

    st.subheader("Master Loop Log (Segment)")
    # extract between markers if present
    match = re.search(r"(?:=== GIWANOS Master Loop Start ===)(.*?)(?:=== GIWANOS Master Loop End ===)", full_log, re.DOTALL)
    if match:
        seg = "=== GIWANOS Master Loop Start ===" + match.group(1) + "=== GIWANOS Master Loop End ==="
    else:
        seg = "\n".join(full_log.splitlines()[-20:])
    st.text_area("Segment", value=seg, height=250)
    st.download_button("Download Full Log", data=full_log, file_name="master_loop_execution.log", mime="text/plain")
else:
    st.error(f"Log file not found: {log_path}")
    st.stop()

st.markdown("---")

# Parse performance entries
perf_pattern = re.compile(r"\[perf\]\s*cpu=(?P<cpu>[0-9]+\.?[0-9]*),\s*mem=(?P<mem>[0-9]+\.?[0-9]*),\s*disk=(?P<disk>[0-9]+\.?[0-9]*)")
entries = []
for line in full_log.splitlines():
    m = perf_pattern.search(line)
    if m:
        timestamp = line.split("]")[0].split(" [")[0].replace(",", ".")
        try:
            dt = datetime.fromisoformat(timestamp)
        except:
            continue
        entries.append({
            "time": dt,
            "cpu": float(m.group("cpu")),
            "memory": float(m.group("mem")),
            "disk": float(m.group("disk"))
        })

st.subheader("Historical System Metrics")
if entries:
    df = pd.DataFrame(entries).sort_values("time")
    df_m = df.melt(id_vars="time", value_vars=["cpu","memory","disk"], var_name="Metric", value_name="Usage")
    fig = px.line(df_m, x="time", y="Usage", color="Metric", markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No [perf] entries found in log.")
