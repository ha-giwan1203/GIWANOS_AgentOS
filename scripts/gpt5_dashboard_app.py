#!/usr/bin/env python3
# [ACTIVE] VELOS-GPT5 통합 모니터링 대시보드 실행 스크립트
# 실행: streamlit run scripts/gpt5_dashboard_app.py

import sys
from pathlib import Path

# VELOS 루트 경로를 Python 경로에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# 기존 VELOS 대시보드 설정 로드
from scripts.velos_dashboard import load_env_file
from modules.gpt5_dashboard import create_gpt5_dashboard_app

def main():
    """GPT-5 대시보드 앱 실행"""
    # 환경변수 로드
    load_env_file()
    
    # 대시보드 앱 실행
    create_gpt5_dashboard_app()

if __name__ == "__main__":
    main()