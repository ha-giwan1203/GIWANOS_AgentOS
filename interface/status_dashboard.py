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

# Page config
st.set_page_config(page_title="GIWANOS 시스템 상태 대시보드", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>GIWANOS 시스템 상태 대시보드</h1>", unsafe_allow_html=True)

# System metrics
cpu_now = psutil.cpu_percent()
mem_now = psutil.virtual_memory().percent
disk_now = psutil.disk_usage("C:/giwanos").percent

# Layout columns
col1, col2, col3, col4, col5 = st.columns(5)

# CPU Usage with color
cpu_color = "red" if cpu_now > 80 else "green"
col1.markdown(f"<div style='text-align:center;'><span style='font-size:24px; color:{cpu_color};'>CPU Usage<br><b>{cpu_now:.1f}%</b></span></div>", unsafe_allow_html=True)
col2.metric("Memory Usage", f"{mem_now:.1f}%")
col3.metric("Disk Usage", f"{disk_now:.1f}%")

# Placeholder for rules/fallback – replace with real values
rules_count = 20
fallback_count = 19
fallback_rate = (fallback_count / rules_count * 100) if rules_count else 0
col4.metric("Judgment Rules", rules_count)
col4.metric("Fallback Count", fallback_count)
col4.metric("Fallback Rate", f"{fallback_rate:.1f}%")

# Latest report
reports_dir = "C:/giwanos/data/reports"
latest_report = max(os.listdir(reports_dir)) if os.path.isdir(reports_dir) else "N/A"
col5.metric("Latest Report", latest_report)

st.markdown("---")

# Recent Master Loop Log
st.subheader("Recent Master Loop Log")
log_path = "C:/giwanos/data/logs/master_loop_execution.log"
if os.path.exists(log_path):
    lines = open(log_path, "r", encoding="utf-8").read().splitlines()
    # extract between start/end
    try:
        start = lines.index("=== GIWANOS Master Loop Start ===")
        end = lines.index("=== GIWANOS Master Loop End ===")
        segment = lines[start:end+1]
    except ValueError:
        segment = lines[-20:]
    st.text_area("Master Loop Log", "
".join(segment), height=200)
    with open(log_path, "r", encoding="utf-8") as f:
        st.download_button("Download Master Log", f, file_name="master_loop_execution.log")
else:
    st.warning("Master loop log not found.")

st.markdown("---")

# Historical System Metrics
st.subheader("Historical System Metrics")
perf_entries = []
if os.path.exists(log_path):
    pattern = re.compile(r"\[perf\] cpu=(?P<cpu>\d+\.\d+), mem=(?P<mem>\d+\.\d+), disk=(?P<disk>\d+\.\d+)")
    for line in open(log_path, "r", encoding="utf-8"):
        match = pattern.search(line)
        if match:
            ts = line.split(" ")[0] + " " + line.split(" ")[1]
            try:
                dt = datetime.fromisoformat(ts)
            except:
                continue
            perf_entries.append({"time": dt, "cpu": float(match.group("cpu")), "memory": float(match.group("mem")), "disk": float(match.group("disk"))})
if perf_entries:
    df = pd.DataFrame(perf_entries)
    fig = px.line(df, x="time", y=["cpu","memory","disk"], labels={"value":"Usage (%)","variable":"Metric"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No performance entries found in logs.")
