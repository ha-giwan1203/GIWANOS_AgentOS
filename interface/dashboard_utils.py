# VELOS 대시보드 유틸리티

import os
import json
from datetime import datetime

def load_dashboard_data(summary_file_path, tab_key):
    try:
        with open(summary_file_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        summary = {}

    if tab_key == "status":
        return {
            "cpu_usage": summary.get("cpu_usage", "N/A"),
            "memory_usage": summary.get("memory_usage", "N/A"),
            "disk_usage": summary.get("disk_usage", "N/A"),
        }
    elif tab_key == "evaluation":
        return summary.get("evaluation_scores", [])
    elif tab_key == "reports":
        return summary.get("reports", [])
    else:
        return {}

def load_memory_summary(summary_file):
    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
        return summary.get("memory", [])
    except Exception as e:
        print(f"[Error] memory 요약 파일 로드 실패: {e}")
        return []

def get_mock_dashboard_status():
    return {
        "cpu_usage": "10.5%",
        "memory_usage": "50.5%",
        "disk_usage": "82.9%"
    }
