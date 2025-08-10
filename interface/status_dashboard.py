# status_dashboard.py - 시스템 상태만 단독 표시 (하드코딩 제거)

import streamlit as st
import json
from modules.core.config import path

st.set_page_config(layout="wide", page_title="시스템 상태")
st.title("🩺 VELOS 시스템 상태 점검")

status_path = path("data", "reports", "summary_dashboard.json")

if status_path.exists():
    data = json.loads(status_path.read_text(encoding="utf-8"))
    st.subheader("📊 현재 상태")
    st.json(data.get("system_status", {}))
else:
    st.warning("시스템 상태 요약 파일이 없습니다.")

