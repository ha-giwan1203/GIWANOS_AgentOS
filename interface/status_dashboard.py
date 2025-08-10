# status_dashboard.py - 시스템 상태만 단독 표시하는 버전

import streamlit as st
import json
from pathlib import Path

st.set_page_config(layout="wide", page_title="시스템 상태")

st.title("🩺 VELOS 시스템 상태 점검")

status_path = Path("C:/giwanos/data/reports/summary_dashboard.json")

if status_path.exists():
    with open(status_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        status = data.get("system_status", {})
        st.subheader("📊 현재 상태")
        st.json(status)
else:
    st.warning("시스템 상태 요약 파일이 없습니다.")


