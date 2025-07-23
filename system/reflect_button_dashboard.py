import streamlit as st
import os
from agent_logger import save_agent_status
from giwanos_agent.reflect_agent import run as run_reflect
from giwanos_agent.report_agent import run as run_report
from giwanos_agent.self_check_agent import run as run_selfcheck

st.set_page_config(page_title="GIWANOS 대시보드", layout="wide")
st.title("🧠 GIWANOS 대시보드")

if st.button("📄 회고 생성"):
    try:
        run_reflect()
        save_agent_status("reflect", "success")
        st.success("회고 생성 완료")
    except Exception as e:
        st.error(f"실패: {e}")
        save_agent_status("reflect", "failed", {"error": str(e)})

if st.button("📤 보고서 전송"):
    try:
        run_report()
        save_agent_status("report", "success")
        st.success("보고서 전송 완료")
    except Exception as e:
        st.error(f"실패: {e}")
        save_agent_status("report", "failed", {"error": str(e)})

if st.button("🩺 시스템 점검"):
    try:
        run_selfcheck()
        save_agent_status("selfcheck", "success")
        st.success("시스템 상태 점검 완료")
    except Exception as e:
        st.error(f"실패: {e}")
        save_agent_status("selfcheck", "failed", {"error": str(e)})
