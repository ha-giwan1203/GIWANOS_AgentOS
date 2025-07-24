
import streamlit as st
import os
from datetime import datetime

def main():
    st.title("GIWANOS 시스템 현황 대시보드 🚀")

    summary_dir = "C:/giwanos/summaries"
    week_number = datetime.now().isocalendar().week
    year = datetime.now().year
    summary_file = os.path.join(summary_dir, f"weekly_summary_{year}W{week_number}.md")

    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as file:
            summary_content = file.read()
        st.markdown(summary_content)
    else:
        st.error("❌ 최신 요약 파일을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
