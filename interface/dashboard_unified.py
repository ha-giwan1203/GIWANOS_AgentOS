
import streamlit as st
from dashboard_utils import (
    load_status, load_md_file_list,
    load_md_content, save_md_content,
    convert_md_to_pdf, render_loop_history
)
from config import REFLECTION_MD_DIR

st.set_page_config(layout="wide")
st.title("🧠 GIWANOS 통합 대시보드")

# 시스템 상태 표시
status = load_status()
with st.expander("📊 시스템 상태 요약", expanded=True):
    st.json(status, expanded=False)

# 회고 파일 선택
st.subheader("📘 GIWANOS 회고 보고서")
selected_file = st.selectbox("회고파일 선택", ["None"] + load_md_file_list())

if selected_file and selected_file != "None":
    content = load_md_content(selected_file)
    edited = st.text_area("회고 내용 편집", content, height=300, key="editor")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 저장"):
            save_md_content(selected_file, edited)
            st.success(f"{selected_file} 저장 완료.")
    with col2:
        if st.button("⬇️ PDF로 저장"):
            pdf_path = convert_md_to_pdf(selected_file, edited)
            st.success(f"PDF 저장 완료: {pdf_path}")

    # 미리보기 영역
    st.markdown("---")
    st.subheader("🪞 미리보기 (Markdown)")
    st.markdown(edited, unsafe_allow_html=True)

# 루프 로그 표시
st.subheader("🔁 루프 실행 기록")
render_loop_history()


