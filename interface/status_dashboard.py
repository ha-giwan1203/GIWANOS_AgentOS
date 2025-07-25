import streamlit as st
import pandas as pd
import os
import json

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 로그 파일 경로
log_file_path = os.path.join(base_dir, 'logs', 'master_loop_execution.log')
agent_log_path = os.path.join(base_dir, 'agent_logs', 'judge_agent.log')

# 회고 파일 경로
reflection_dir = os.path.join(base_dir, 'reflection_md')

# 평가 데이터 경로
evaluation_score_path = os.path.join(base_dir, 'memory', 'loop_evaluation_score.json')

# 시스템 상태 데이터 경로
report_status_path = os.path.join(base_dir, 'memory', 'report_status.json')
loop_history_path = os.path.join(base_dir, 'memory', 'loop_history.csv')

st.title('GIWANOS 고도화 대시보드 📊')

# 로그 파일 표시
st.header('📄 최근 로그')
if os.path.exists(log_file_path):
    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        logs = file.readlines()
        st.text_area("Master 루프 실행 로그", ''.join(logs[-20:]), height=200)
else:
    st.warning('Master 로그 파일이 존재하지 않습니다.')

if os.path.exists(agent_log_path):
    with open(agent_log_path, 'r', encoding='utf-8', errors='ignore') as file:
        agent_logs = file.readlines()
        st.text_area("JudgeAgent 실행 로그", ''.join(agent_logs[-20:]), height=200)
else:
    st.warning('JudgeAgent 로그 파일이 존재하지 않습니다.')

# 회고 파일 표시
st.header('📝 최근 회고 파일')
reflection_files = sorted(os.listdir(reflection_dir), reverse=True)
if reflection_files:
    latest_reflection = reflection_files[0]
    with open(os.path.join(reflection_dir, latest_reflection), 'r', encoding='utf-8', errors='ignore') as file:
        reflection_content = file.read()
        st.markdown(reflection_content)
else:
    st.warning('회고 파일이 존재하지 않습니다.')

# 평가 데이터 표시
st.header('📊 최근 평가 데이터')
if os.path.exists(evaluation_score_path):
    with open(evaluation_score_path, 'r', encoding='utf-8', errors='ignore') as file:
        evaluation_scores = json.load(file)
        st.json(evaluation_scores)
else:
    st.warning('평가 데이터 파일이 존재하지 않습니다.')

# 시스템 상태 데이터 표시
st.header('🔧 최근 시스템 상태')
if os.path.exists(report_status_path):
    with open(report_status_path, 'r', encoding='utf-8', errors='ignore') as file:
        report_status = json.load(file)
        st.json(report_status)
else:
    st.warning('시스템 상태 파일이 존재하지 않습니다.')

if os.path.exists(loop_history_path):
    loop_history_df = pd.read_csv(loop_history_path, encoding='utf-8', encoding_errors='ignore')
    st.dataframe(loop_history_df)
else:
    st.warning('루프 히스토리 파일이 존재하지 않습니다.')