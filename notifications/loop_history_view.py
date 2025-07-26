
import streamlit as st
import pandas as pd
from pathlib import Path

def render_loop_history():
    st.markdown("## 🔄 루프 로그 히스토리")

    log_path = Path("logs/loop_history.csv")
    if log_path.exists():
        df = pd.read_csv(log_path)
        st.dataframe(df, use_container_width=True)
    else:
        st.error(f"loop_history.csv 파일이 존재하지 않습니다: {log_path}")
