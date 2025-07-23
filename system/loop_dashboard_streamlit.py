import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import streamlit as st
import json
import os

st.set_page_config(page_title="GIWANOS 루프 대시보드", layout="wide")
st.title("📊 GIWANOS 루프 실행 시각화")

# 데이터 로딩
if not os.path.exists("loop_dashboard_data.json"):
    st.warning("loop_dashboard_data.json 파일이 없습니다.")
else:
    with open("loop_dashboard_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for loop, stats in data.items():
        with st.expander(f"🌀 {loop}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("성공", stats.get("success", 0))
            col2.metric("실패", stats.get("failures", 0))
            col3.write(f"🕒 마지막 실행: {stats.get('last_run', 'N/A')}")
            st.write(f"🧑 담당자: {stats.get('assigned', '미지정')}")


# 회고 로그 통합 시각화
st.subheader("🧠 회고 결과 요약")
if os.path.exists("loop_reflection_live_log.json"):
    with open("loop_reflection_live_log.json", "r", encoding="utf-8") as f:
        log = json.load(f)
        for loop_name, item in log.items():
            with st.expander(f"🌀 {loop_name} 회고"):
                st.markdown(f"**실행 시각:** {item['executed_at']}")
                st.markdown(f"🧠 {item['gpt_comment']}")
else:
    st.info("회고 로그 파일(loop_reflection_live_log.json)이 아직 없습니다.")
