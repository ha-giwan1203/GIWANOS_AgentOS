#!/usr/bin/env python3
# [ACTIVE] VELOS-GPT5 통합 모니터링 대시보드 (기존 velos_dashboard.py 대체)
# 실행: streamlit run velos_dashboard.py

import sys
from pathlib import Path

# VELOS 루트 경로를 Python 경로에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# 환경변수 로드 함수
def load_env_file():
    """환경 파일 로드"""
    env_file = Path("/home/user/webapp/.env")
    if env_file.exists():
        try:
            import os
            content = env_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        except Exception:
            pass

# GPT-5 대시보드 앱 실행
from modules.gpt5_dashboard import create_gpt5_dashboard_app

def main():
    """GPT-5 대시보드 앱 실행 (기존 VELOS 대시보드 교체)"""
    # 환경변수 로드
    load_env_file()
    
    # GPT-5 통합 모니터링 대시보드 실행
    create_gpt5_dashboard_app()

if __name__ == "__main__":
    main()