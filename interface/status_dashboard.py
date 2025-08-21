# [ACTIVE] VELOS 상태 대시보드 - 시스템 모니터링 인터페이스
# -*- coding: utf-8 -*-
# [ACTIVE] VELOS 운영 철학 선언문
# "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

# VELOS 상태 대시보드
# - 시스템 상태 모니터링
# - 실시간 상태 표시
# - 간단한 상태 체크

import json
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# VELOS 루트 경로
VELOS_ROOT = Path(r"C:\giwanos")


def check_system_status():
    """시스템 상태 확인"""
    status = {
        "velos_root": VELOS_ROOT.exists(),
        "database": (VELOS_ROOT / "data" / "velos.db").exists(),
        "logs": (VELOS_ROOT / "data" / "logs").exists(),
        "configs": (VELOS_ROOT / "configs").exists(),
        "scripts": (VELOS_ROOT / "scripts").exists(),
        "modules": (VELOS_ROOT / "modules").exists(),
    }
    return status


def main():
    """메인 대시보드"""
    st.title("VELOS 상태 대시보드")
    st.write("시스템 상태 모니터링")

    # 상태 확인
    status = check_system_status()

    # 상태 표시
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("핵심 디렉토리")
        for name, exists in status.items():
            if exists:
                st.success(f"✅ {name}")
            else:
                st.error(f"❌ {name}")

    with col2:
        st.subheader("시스템 정보")
        st.write(f"**VELOS 루트**: {VELOS_ROOT}")
        st.write(f"**현재 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 자동 새로고침
        if st.button("새로고침"):
            st.rerun()

    # 자동 새로고침 (5초마다)
    time.sleep(5)
    st.rerun()


if __name__ == "__main__":
    main()
