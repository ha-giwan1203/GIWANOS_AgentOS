# streamlit_summary_dashboard.py - 보고서 요약만 단독 표시하는 버전

import streamlit as st
import json
from pathlib import Path

st.set_page_config(layout="wide", page_title="보고서 요약")

st.title("🧾 VELOS 주간 보고서 요약")

summary_path = Path("C:/giwanos/data/reports/summary_dashboard.json")

if summary_path.exists():
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        summary = data.get("weekly_summary", {}).get("markdown", "요약이 없습니다.")
        st.markdown(summary)
else:
    st.warning("요약 파일이 존재하지 않습니다.")


