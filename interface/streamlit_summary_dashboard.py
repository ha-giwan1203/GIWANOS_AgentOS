import streamlit as st
import os
from pathlib import Path

st.set_page_config(page_title="GIWANOS 요약 대시보드", layout="wide")
st.title("📋 주간 회고 요약 보기")

summary_dir = Path("summaries")
if not summary_dir.exists():
    st.warning("summaries 폴더가 없습니다.")
else:
    files = sorted(summary_dir.glob("weekly_summary_*.md"))
    if not files:
        st.info("주간 요약이 아직 없습니다.")
    else:
        selected = st.selectbox("📅 요약 파일 선택", [f.name for f in files])
        st.subheader(f"📄 {selected}")
        st.code(Path(summary_dir / selected).read_text(encoding="utf-8"), language="markdown")
