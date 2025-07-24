
import streamlit as st
import json
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="GIWANOS 평가 대시보드", layout="wide")
st.title("📊 GIWANOS 통합 평가 결과")

log_path = Path("logs/evaluation_aggregated_log.jsonl")

if not log_path.exists():
    st.warning("평가 통합 로그 파일이 없습니다.")
    st.stop()

# Load and parse the JSONL log file
with open(log_path, encoding="utf-8") as f:
    lines = [json.loads(line) for line in f if line.strip()]

# Convert to DataFrame
df = pd.DataFrame(lines)

# 날짜 필터
df["timestamp"] = pd.to_datetime(df["timestamp"])
start_date = st.date_input("시작 날짜", df["timestamp"].min().date())
end_date = st.date_input("종료 날짜", df["timestamp"].max().date())
df = df[(df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)]

# 타입 필터
types = st.multiselect("평가 타입 필터", df["type"].unique(), default=list(df["type"].unique()))
df = df[df["type"].isin(types)]

# 점수 필터 (RAG만 해당)
if "score" in df.columns:
    score_range = st.slider("평가 점수 범위", 1, 5, (1, 5))
    df = df[df["score"].fillna(0).between(score_range[0], score_range[1])]

# 표 출력
st.subheader("📋 필터링된 평가 결과")
st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)
