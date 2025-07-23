import os
import streamlit as st

# ————————————————————————————————
# CONFIGURATION
# ————————————————————————————————
REFLECT_DIR = os.path.join(os.getcwd(), "reflection_md")

# Utility: get all .md files in the reflection directory
@st.cache_data(show_spinner=False)
def list_md_files():
    if not os.path.isdir(REFLECT_DIR):
        return []
    return sorted(f for f in os.listdir(REFLECT_DIR) if f.endswith(".md"))

# ————————————————————————————————
# APP LAYOUT
# ————————————————————————————————
st.set_page_config(page_title="GIWANOS 통합 대시보드", layout="wide")
st.title("GIWANOS 통합 대시보드")

# 1) System summary (just a placeholder for now)
st.subheader("시스템 상태 요약")
st.json({
    "generated_at": "2025-07-22T02:08:39.903803",
    "latest_md": "loop_reflection_log.md",
    "recent_backups": ["giwanos_backup_20250721_130423.zip", "giwanos_backup_20250721_103957.zip"],
    "memory_issues": [],
    "next_tasks": []
})

st.markdown("---")

# 2) 회고 파일 선택 & 편집
st.subheader("GIWANOS 회고 보고서")

md_files = list_md_files()
selected = st.selectbox("회고 파일 선택", [""] + md_files)

if selected:
    file_path = os.path.join(REFLECT_DIR, selected)
    content = ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        st.error(f"파일이 없습니다: {file_path}")
    else:
        edited = st.text_area("회고 내용 편집", value=content, height=400)

        if st.button("저장"):
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(edited)
                st.success(f"{selected} 파일이 성공적으로 저장되었습니다.")
            except Exception as e:
                st.error(f"저장 실패: {e}")

st.markdown("---")

# 3) 루프 흐름 (history)
st.subheader("루프 흐름")
# Dummy table for now
import pandas as pd
df = pd.DataFrame([
    {"timestamp": "2025-07-19T07:28:56", "loop": "sort_done", "success": "success", "details": None},
])
st.dataframe(df, use_container_width=True)
