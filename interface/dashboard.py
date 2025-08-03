import streamlit as st
import os, json
from datetime import datetime, date

# --- 설정 ---
BASE_DIR = os.getcwd()
STATUS_SUMMARY_PATH = os.path.join(BASE_DIR, 'giwanos_status_summary.json')
REFLECTION_LOG_DIR = os.path.join(BASE_DIR, 'summaries')

# --- 데이터 로드 함수 ---
def load_status():
    with open(STATUS_SUMMARY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_reflections():
    items=[]
    for fn in os.listdir(REFLECTION_LOG_DIR):
        if fn.endswith('.md') and not fn.startswith('weekly_summary_'):
            items.append(fn)
    return sorted(items)

@st.cache_data
def load_weekly():
    items=[]
    for fn in os.listdir(REFLECTION_LOG_DIR):
        if fn.startswith('weekly_summary_') and fn.endswith('.md'):
            items.append(fn)
    return sorted(items)

# --- 앱 ---
st.title('GIWANOS 통합 대시보드')
tabs = st.tabs(['전체 회고 탐색', '주간 회고 요약'])

# Tab 1: 전체 회고 탐색
with tabs[0]:
    st.subheader('시스템 상태 요약')
    st.json(load_status())
    st.markdown('---')
    st.subheader('회고 목록')
    all_refs = load_reflections()
    choice = st.selectbox('회고 파일 선택', all_refs)
    if choice:
        path = os.path.join(REFLECTION_LOG_DIR, choice)
        st.markdown(open(path, 'r', encoding='utf-8').read())

# Tab 2: 주간 요약
with tabs[1]:
    st.subheader('주간 회고 요약')
    weekly = load_weekly()
    choice2 = st.selectbox('주간 요약 선택', weekly)
    if choice2:
        path2 = os.path.join(REFLECTION_LOG_DIR, choice2)
        st.markdown(open(path2, 'r', encoding='utf-8').read())
