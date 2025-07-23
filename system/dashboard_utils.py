import streamlit as st
import os
import pandas as pd

# 자동 경로 지정: 프로젝트 루트 기준
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
LOG_PATH = os.path.join(ROOT_DIR, "logs", "loop_history.csv")

def render_loop_history():
    if not os.path.exists(LOG_PATH):
        st.warning(f"❌ 로그 파일이 존재하지 않습니다: {LOG_PATH}")
        return
    df = pd.read_csv(LOG_PATH)
    st.dataframe(df)

def main():
    st.set_page_config(layout="wide", page_title="GIWANOS 루프 대시보드")
    st.title("🌀 루프 로그 히스토리")
    render_loop_history()

if __name__ == "__main__":
    main()
