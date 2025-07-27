import os
import sys
from pathlib import Path
import streamlit as st
import psutil
import glob
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh

# core 모듈 경로 설정
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.log_manager import setup_logging
from core.judgment_rules_manager import load_rules
from core.fallback_stats_manager import load_stats

# UTF-8 환경 보장
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

logger = setup_logging("streamlit", "streamlit.log")

# 자동 갱신 설정 (30초마다)
st_autorefresh(interval=30000)

def main():
    st.set_page_config(page_title="GIWANOS 시스템 상태", layout="wide")
    st.title("GIWANOS 시스템 상태 대시보드")

    # 시스템 메트릭
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage(str(ROOT_DIR)).percent
    rules = load_rules()
    rule_count = len(rules) if isinstance(rules, list) else 1

    # 메타인지 통계
    stats = load_stats()
    fallbacks = stats.get('fallbacks', 0)
    evals = stats.get('evaluations', 0)
    if evals > 0:
        avg_conf = stats.get('sum_confidence', 0.0) / evals
        fallback_rate = fallbacks / evals
    else:
        avg_conf = 0.0
        fallback_rate = 0.0

    col1, col2, col3 = st.columns(3)

    def metric_alert(metric, value, threshold):
        if value >= threshold:
            return f":red[{value}% 🚨]"
        return f"{value}%"

    col1.metric("CPU Usage", metric_alert("CPU", cpu, 80))
    col1.metric("Memory Usage", metric_alert("Memory", mem, 80))
    col1.metric("Disk Usage", metric_alert("Disk", disk, 90))
    col2.metric("Judgment Rules", rule_count)
    col2.metric("Fallback Count", fallbacks)
    col2.metric("Fallback Rate", f"{fallback_rate:.1%}")
    col3.metric("Avg Confidence", f"{avg_conf:.2f}")

    # 최신 보고서
    report_files = glob.glob(str(ROOT_DIR / 'data' / 'reports' / 'weekly_report_*.pdf'))
    latest = Path(max(report_files, key=os.path.getmtime)).name if report_files else "No report"
    col3.write(f"**Latest Report:** {latest}")

    # 최근 로그 및 다운로드 기능
    st.subheader("Recent Logs")
    log_master = ROOT_DIR / "logs" / "master_loop.log"
    log_streamlit = ROOT_DIR / "logs" / "streamlit.log"

    def read_last_lines(file_path, n=10):
        if not file_path.exists():
            return ["Log file not found"]
        return file_path.read_text(encoding='utf-8').splitlines()[-n:]

    master_log = read_last_lines(log_master)
    streamlit_log = read_last_lines(log_streamlit)

    st.write("**Master Loop Log**")
    st.code("\n".join(master_log), language="text")
    st.download_button("Download Master Log", data="\n".join(master_log), file_name="master_loop.log")

    st.write("**Streamlit Log**")
    st.code("\n".join(streamlit_log), language="text")
    st.download_button("Download Streamlit Log", data="\n".join(streamlit_log), file_name="streamlit.log")

    # 역사적 데이터 시각화 (최근 1시간, 5분 단위)
    st.subheader("Historical Metrics (Last 1 Hour)")
    times = [datetime.datetime.now() - datetime.timedelta(minutes=5*i) for i in range(12)][::-1]
    metrics = pd.DataFrame({
        'Time': [t.strftime("%H:%M") for t in times],
        'CPU': [psutil.cpu_percent(interval=0.5) for _ in times],
        'Memory': [psutil.virtual_memory().percent for _ in times],
        'Disk': [psutil.disk_usage(str(ROOT_DIR)).percent for _ in times]
    })
    metrics.set_index('Time', inplace=True)
    st.line_chart(metrics)

    logger.info("Dashboard rendered with enhanced features.")

if __name__ == "__main__":
    main()