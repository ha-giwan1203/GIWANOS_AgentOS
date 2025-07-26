
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 기존 경로 유지
log_file_path = os.path.join(base_dir, 'logs', 'master_loop_execution.log')
agent_log_path = os.path.join(base_dir, 'agent_logs', 'judge_agent.log')
reflection_dir = os.path.join(base_dir, 'reflection_md')
evaluation_score_path = os.path.join(base_dir, 'memory', 'loop_evaluation_score.json')
report_status_path = os.path.join(base_dir, 'memory', 'report_status.json')
loop_history_path = os.path.join(base_dir, 'memory', 'loop_history.csv')

# 추가된 경로 (장애 및 복구 기록)
failure_flag_path = os.path.join(base_dir, 'data', 'logs', 'failure_detected.flag')
recovery_log_path = os.path.join(base_dir, 'data', 'logs', 'recovery_log.json')
performance_metrics_path = os.path.join(base_dir, 'memory', 'learning_memory.json')

st.title('GIWANOS 고도화 대시보드 📊')

tab1, tab2, tab3, tab4 = st.tabs(["📄 로그 및 회고", "📊 평가 데이터", "⚠️ 장애 상태", "📈 성능 지표"])

with tab1:
    st.header('📄 최근 로그')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            logs = file.readlines()
            st.text_area("Master 루프 실행 로그", ''.join(logs[-20:]), height=150)
    else:
        st.warning('Master 로그 파일이 존재하지 않습니다.')

    if os.path.exists(agent_log_path):
        with open(agent_log_path, 'r', encoding='utf-8', errors='ignore') as file:
            agent_logs = file.readlines()
            st.text_area("JudgeAgent 실행 로그", ''.join(agent_logs[-20:]), height=150)
    else:
        st.warning('JudgeAgent 로그 파일이 존재하지 않습니다.')

    st.header('📝 최근 회고 파일')
    reflection_files = sorted(os.listdir(reflection_dir), reverse=True)
    if reflection_files:
        latest_reflection = reflection_files[0]
        with open(os.path.join(reflection_dir, latest_reflection), 'r', encoding='utf-8', errors='ignore') as file:
            reflection_content = file.read()
            st.markdown(reflection_content)
    else:
        st.warning('회고 파일이 존재하지 않습니다.')

with tab2:
    st.header('📊 최근 평가 데이터')
    if os.path.exists(evaluation_score_path):
        with open(evaluation_score_path, 'r', encoding='utf-8', errors='ignore') as file:
            evaluation_scores = json.load(file)
            st.json(evaluation_scores)
    else:
        st.warning('평가 데이터 파일이 존재하지 않습니다.')

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

with tab3:
    st.header('⚠️ 장애 상태')
    if os.path.exists(failure_flag_path):
        st.error('🚨 장애 상태 발생 중!')
        with open(failure_flag_path, 'r', encoding='utf-8') as file:
            failure_time = file.read()
            st.write(f"발생 시간: {failure_time}")
    else:
        st.success('✅ 현재 장애 상태가 없습니다.')

    st.header('🛠️ 최근 복구 이력')
    if os.path.exists(recovery_log_path):
        with open(recovery_log_path, 'r', encoding='utf-8') as file:
            recovery_logs = json.load(file)
            st.dataframe(pd.DataFrame(recovery_logs))
    else:
        st.info('복구 기록이 존재하지 않습니다.')

with tab4:
    st.header('📈 최근 성능 지표')
    if os.path.exists(performance_metrics_path):
        with open(performance_metrics_path, 'r', encoding='utf-8') as file:
            performance_data = json.load(file).get('performance_metrics', [])
            if performance_data:
                performance_df = pd.DataFrame(performance_data)
                st.line_chart(performance_df.set_index('timestamp')[['accuracy', 'response_time_sec']])
                st.dataframe(performance_df)
            else:
                st.info('성능 지표 데이터가 없습니다.')
    else:
        st.warning('성능 지표 파일이 존재하지 않습니다.')
