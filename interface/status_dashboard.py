# C:/giwanos/interface/status_dashboard.py

import os
import psutil
import streamlit as st
from datetime import datetime
import plotly.express as px
import pandas as pd

# Page config
st.set_page_config(page_title="GIWANOS 시스템 상태 대시보드", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>GIWANOS 시스템 상태 대시보드</h1>", unsafe_allow_html=True)

# Metrics
cpu = psutil.cpu_percent()
mem = psutil.virtual_memory().percent
disk = psutil.disk_usage("C:/giwanos").percent

col1, col2, col3, col4, col5 = st.columns(5)

# Colored CPU metric
cpu_color = "red" if cpu > 80 else "green"
col1.markdown(f"<div style='text-align:center;'><span style='font-size:24px;color:{cpu_color};'>CPU Usage<br><b>{cpu:.1f}%</b></span></div>", unsafe_allow_html=True)

# Memory and Disk
col2.metric("Memory Usage", f"{mem:.1f}%")
col3.metric("Disk Usage", f"{disk:.1f}%")

# Placeholder values for rules and fallback
# In production, replace with actual logic or data load
rules_count = 20
fallback_count = 19
fallback_rate = f"{(fallback_count/rules_count*100):.1f}%"

col4.metric("Judgment Rules", rules_count)
col4.metric("Fallback Count", fallback_count)
col4.metric("Fallback Rate", fallback_rate)

# Latest report and confidence
# Fetch latest report file
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
    lines = open(log_path, "r", encoding="utf-8").read().splitlines()[-10:]
    st.code("\n".join(lines), language='text')
    with open(log_path, "r", encoding="utf-8") as f:
        st.download_button("Download Master Log", f, file_name="master_loop_execution.log")
else:
    st.warning("Master loop log not found.")

st.markdown("---")

# Historical Metrics Chart
st.subheader("Historical CPU Usage (Last 1 Hour)")
# Simulate sample data; in production read from time-series store
times = [datetime.now()]
values = [cpu]
df = pd.DataFrame({"time": times, "cpu": values})
fig = px.line(df, x="time", y="cpu", labels={"cpu":"CPU %", "time":"Time"})
st.plotly_chart(fig, use_container_width=True)
