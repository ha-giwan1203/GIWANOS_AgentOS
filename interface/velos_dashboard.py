
import streamlit as st
import os
import json
import pandas as pd
import psutil
import subprocess
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="VELOS Dashboard", layout="wide")
st.title("📊 VELOS 시스템 대시보드")

TABS = ["시스템 상태", "주간 보고서", "Memory Insight Viewer", "마스터 루프 실행", "사고 성능 분석"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(TABS)

BASE_DIR = "C:/giwanos"

with tab1:
    st.header("🖥 시스템 상태")

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    st.metric("CPU 사용률", f"{cpu}%")
    st.metric("메모리 사용률", f"{memory.percent}%")
    st.metric("디스크 사용률", f"{disk.percent}%")

with tab2:
    st.header("🗂 최근 보고서")

    reports_dir = os.path.join(BASE_DIR, "data", "reports")
    reports = [f for f in os.listdir(reports_dir) if f.endswith(".pdf") or f.endswith(".md")]
    reports = sorted(reports, reverse=True)

    if reports:
        for report in reports[:20]:
            st.write(f"📄 {report}")
    else:
        st.warning("보고서를 찾을 수 없습니다.")

with tab3:
    st.header("🧠 GPT 판단 메모리")

    memory_path = os.path.join(BASE_DIR, "data", "memory", "learning_memory.json")

    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            insights = data.get("insights", [])
            if insights:
                df = pd.DataFrame(insights)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values(by="timestamp", ascending=False)
                st.dataframe(df, use_container_width=True)
                keyword = st.text_input("🔍 키워드로 필터링")
                if keyword:
                    filtered = df[df["insight"].str.contains(keyword, case=False, na=False)]
                    st.write(f"🔎 {len(filtered)}건 결과")
                    st.dataframe(filtered)
            else:
                st.info("저장된 판단 기록이 없습니다.")
        except Exception as e:
            st.error(f"메모리 파일 로딩 실패: {e}")
    else:
        st.warning("learning_memory.json 파일이 존재하지 않습니다.")

with tab4:
    st.header("▶ 마스터 루프 수동 실행")

    run_button = st.button("🌀 VELOS Master Loop 실행")

    if run_button:
        with st.spinner("루프 실행 중..."):
            try:
                result = subprocess.run(
                    ["python", "scripts/run_giwanos_master_loop.py"],
                    capture_output=True, text=True, timeout=300
                )
                st.success("✅ 루프 실행 완료")
                st.code(result.stdout)
            except Exception as e:
                st.error(f"루프 실행 실패: {e}")

with tab5:
    st.header("🧪 사고 성능 분석")

    cot_scores = [
        {"date": "2025-07-27", "score": 92.5},
        {"date": "2025-07-28", "score": 93.8},
        {"date": "2025-07-30", "score": 94.4},
        {"date": "2025-08-01", "score": 95.2},
        {"date": "2025-08-04", "score": 95.2},
    ]

    df_cot = pd.DataFrame(cot_scores)
    df_cot["date"] = pd.to_datetime(df_cot["date"])

    fig1, ax1 = plt.subplots()
    ax1.plot(df_cot["date"], df_cot["score"], marker='o', linestyle='-', color='cyan')
    ax1.set_title("CoT 평가 점수 추이")
    ax1.set_xlabel("날짜")
    ax1.set_ylabel("점수")
    ax1.grid(True)
    st.pyplot(fig1)

    api_efficiency = [
        {"date": "2025-07-27", "calls": 105, "reduction": 40},
        {"date": "2025-07-28", "calls": 82, "reduction": 55},
        {"date": "2025-07-30", "calls": 60, "reduction": 70},
        {"date": "2025-08-01", "calls": 42, "reduction": 78},
        {"date": "2025-08-04", "calls": 20, "reduction": 80},
    ]

    df_api = pd.DataFrame(api_efficiency)
    df_api["date"] = pd.to_datetime(df_api["date"])

    fig2, ax2 = plt.subplots()
    ax2.bar(df_api["date"].dt.strftime('%m-%d'), df_api["reduction"], color='lightgreen')
    ax2.set_title("API 호출 절감률 (%)")
    ax2.set_xlabel("날짜")
    ax2.set_ylabel("절감률 (%)")
    st.pyplot(fig2)
