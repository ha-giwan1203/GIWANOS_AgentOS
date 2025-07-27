# C:/giwanos/interface/status_dashboard.py

import os
import psutil
import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import ast
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
cpu = psutil.cpu_percent()
mem = psutil.virtual_memory().percent
disk = psutil.disk_usage("C:/giwanos").percent

# Layout columns
col1, col2, col3, col4, col5 = st.columns(5)

# CPU Usage with color
cpu_color = "red" if cpu > 80 else "green"
col1.markdown(
    f"<div style='text-align:center;'><span style='font-size:24px; color:{cpu_color};'>CPU Usage<br><b>{cpu:.1f}%</b></span></div>",
    unsafe_allow_html=True
)
col2.metric("Memory Usage", f"{mem:.1f}%")
col3.metric("Disk Usage", f"{disk:.1f}%")

# Placeholder for rules/fallback – replace with real values
rules_count = 20
fallback_count = 19
fallback_rate = (fallback_count / rules_count * 100) if rules_count else 0
col4.metric("Judgment Rules", rules_count)
col4.metric("Fallback Count", fallback_count)
col4.metric("Fallback Rate", f"{fallback_rate:.1f}%")

reports_dir = "C:/giwanos/data/reports"
latest_report = max(os.listdir(reports_dir)) if os.path.isdir(reports_dir) else "N/A"
avg_confidence = 0.13
col5.metric("Avg Confidence", f"{avg_confidence:.2f}")
col5.markdown(f"**Latest Report:** {latest_report}")

st.markdown("---")

# Recent Master Loop Log
st.subheader("Recent Master Loop Log")
log_path = "C:/giwanos/data/logs/master_loop_execution.log"
if os.path.exists(log_path):
    lines = open(log_path, "r", encoding="utf-8").read().splitlines()
    # show between start/end markers
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

# Historical Metrics Chart
st.subheader("Historical System Metrics")
cpu_data = []
mem_data = []
disk_data = []
if os.path.exists(log_path):
    for line in open(log_path, "r", encoding="utf-8"):
        if "[monitor_performance]" in line or "[check_memory_usage]" in line or "[disk_space_alert]" in line:
            # parse timestamp and payload
            prefix, _, rest = line.partition("] ")
            ts_str = prefix.split(" ")[0] + " " + prefix.split(" ")[1]
            try:
                dt = datetime.fromisoformat(ts_str)
            except:
                continue
            token, _, payload = rest.partition("] ")
            try:
                metrics = ast.literal_eval(payload)
            except:
                continue
            if token == "[monitor_performance":
                cpu_data.append({"time": dt, "value": metrics.get("cpu_percent"), "metric": "CPU"})
            elif token == "[check_memory_usage":
                mem_data.append({"time": dt, "value": metrics if isinstance(metrics, (int,float)) else metrics.get("memory_percent"), "metric": "Memory"})
            elif token == "[disk_space_alert":
                disk_data.append({"time": dt, "value": metrics if isinstance(metrics, (int,float)) else metrics.get("disk_percent"), "metric": "Disk"})

data = cpu_data + mem_data + disk_data
if data:
    df = pd.DataFrame(data)
    fig = px.line(df, x="time", y="value", color="metric", markers=True,
                  labels={"time":"Time","value":"Usage (%)","metric":"Metric"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No performance entries found in logs.")
