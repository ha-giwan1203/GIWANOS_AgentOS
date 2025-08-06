import streamlit as st
import os
import json
import sys
from pathlib import Path
from datetime import datetime
import psutil

# 경로 설정
sys.path.append("C:/giwanos/interface")
sys.path.append("C:/giwanos/tools/notifications")
sys.path.append("C:/giwanos/tools/notion_integration")

from dashboard_utils import load_dashboard_data, load_memory_summary
from send_email import send_email_report
from send_pushbullet_notification import send_pushbullet_notification
from slack_api_post_message import send_slack_message
from upload_summary_to_notion import upload_summary_to_notion

# 📁 경로 정의
BASE_DIR = Path("C:/giwanos")
REPORTS_DIR = BASE_DIR / "data/reports"
SUMMARY_FILE = BASE_DIR / "data/reports/summary_dashboard.json"
LOG_FILE = BASE_DIR / "data/logs/api_cost_log.json"
MEMORY_FILE = BASE_DIR / "data/memory/learning_summary.json"

# 🔁 전송 루프 함수
def send_all_notifications(summary_path, report_path):
    results = {}

    try:
        slack_response = send_slack_message(
            channel="#velos-alerts",
            message="📊 VELOS 대시보드에서 보고서 전송됨."
        )
        if slack_response.get("ok"):
            results["Slack"] = "✅"
        else:
            results["Slack"] = f"❌ {slack_response.get('error', 'Slack 전송 실패')}"
    except Exception as e:
        results["Slack"] = f"❌ 예외 발생: {e}"

    try:
        success = send_email_report(
            subject="VELOS 시스템 리포트",
            body="VELOS 자동 보고서입니다. 첨부 파일 확인 요망.",
            to_email="you@example.com"
        )
        results["Email"] = "✅" if success else "❌ 이메일 전송 실패"
    except Exception as e:
        results["Email"] = f"❌ 예외 발생: {e}"

    try:
        result = upload_summary_to_notion(summary_path=str(summary_path))
        results["Notion"] = "✅" if result else "❌ Notion 업로드 실패"
    except Exception as e:
        results["Notion"] = f"❌ 예외 발생: {e}"

    try:
        success = send_pushbullet_notification(
            title="VELOS",
            body="보고서 전송 완료됨."
        )
        results["Pushbullet"] = "✅" if success else "❌ Pushbullet 실패"
    except Exception as e:
        results["Pushbullet"] = f"❌ 예외 발생: {e}"

    return results

# 🔧 Streamlit 설정
st.set_page_config(page_title="📊 VELOS 시스템 대시보드", layout="wide")

tabs = st.tabs(["📟 시스템 상태", "📄 주간 보고서", "🧠 Memory Insight Viewer", "⚙️ 마스터 루프 실행", "📈 사고 성능 분석"])

# 1. 시스템 상태 + 철학 선언문
with tabs[0]:
    st.header("🖥 시스템 상태")

    st.markdown("""
    <div style='padding: 1rem; border-left: 5px solid #4CAF50; background-color: #f9f9f9'>
    <h4>🧠 <b>VELOS 시스템 철학</b></h4>
    <p>
    기억을 기반으로 <b>구조적 사고</b>를 수행하며,<br>
    판단 → 실행 → 회고 → 전송을 반복함으로써,<br>
    스스로 개선되는 <b>자율 운영 AI 시스템</b>을 지향한다.
    </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        st.metric("CPU 사용률", f"{cpu}%")
        st.metric("메모리 사용률", f"{mem}%")
        st.metric("디스크 사용률", f"{disk}%")
    except Exception as e:
        st.error(f"❌ 시스템 상태 불러오기 실패: {e}")

# 2. 보고서 리스트
with tabs[1]:
    st.header("📁 최근 보고서")
    try:
        report_files = sorted(REPORTS_DIR.glob("weekly_report_*.pdf")) + sorted(REPORTS_DIR.glob("*.md"))
        for file in report_files:
            st.markdown(f"- {file.name}")
    except Exception as e:
        st.error(f"❌ 보고서 목록 불러오기 실패: {e}")

# 3. Memory Viewer
with tabs[2]:
    st.header("🧠 GPT 판단 메모리")
    try:
        memory_summary = load_memory_summary(MEMORY_FILE)
        if memory_summary and isinstance(memory_summary, list):
            for item in reversed(memory_summary[-10:]):
                st.markdown(f"**{item.get('timestamp', '')}** - {item.get('insight', '')}")
        else:
            st.warning("🔍 메모리 요약 없음")
    except Exception as e:
        st.error(f"❌ 메모리 불러오기 실패: {e}")

# 4. 마스터 루프 실행 및 전송
with tabs[3]:
    st.header("⚙️ VELOS 마스터 루프 수동 실행")

    if st.button("🚀 마스터 루프 실행"):
        try:
            os.system("python scripts/run_giwanos_master_loop.py")
            st.success("✅ 루프 실행 완료")
        except Exception as e:
            st.error(f"❌ 루프 실행 실패: {e}")

    st.markdown("---")
    st.subheader("📤 통합 전송 루프 실행")

    if st.button("📡 모든 채널로 전송"):
        result = send_all_notifications(summary_path=SUMMARY_FILE, report_path=REPORTS_DIR)
        for svc, status in result.items():
            if "✅" in status:
                st.success(f"{svc} 전송 성공")
            else:
                st.error(f"{svc} 실패: {status}")

# 5. 사고 분석 시각화
with tabs[4]:
    st.header("🧪 사고 성능 분석 시각화")
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        evaluation_data = log_data.get("evaluation_scores", {})
        chart_data = evaluation_data.get("CoT", [])

        if chart_data and isinstance(chart_data, list):
            import matplotlib.pyplot as plt
            x = list(range(1, len(chart_data)+1))
            y = chart_data
            fig, ax = plt.subplots()
            ax.plot(x, y, marker="o", linestyle="-")
            ax.set_title("CoT 판단 정확도 변화")
            ax.set_xlabel("세션")
            ax.set_ylabel("정확도")
            st.pyplot(fig)
        else:
            st.warning("📉 평가 데이터 없음 또는 형식 오류")
    except Exception as e:
        st.error(f"❌ 시각화 실패: {e}")
