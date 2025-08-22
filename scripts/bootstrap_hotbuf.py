#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "C:\giwanos"

    def get_data_path(*parts):
        return os.path.join("C:\giwanos", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("C:\giwanos", "configs", *parts)

    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"


"""
VELOS Hotbuf Bootstrap Script
핫버퍼 시스템을 초기화하고 세션을 준비합니다.
"""

import os
import sys

# ROOT 경로 설정
ROOT = get_velos_root() if "get_velos_root" in locals() else "C:\giwanos"
if ROOT not in sys.path:
    sys.path.append(ROOT)


def main():
    try:
        from modules.core.hotbuf_manager import session_bootstrap

        print("=== VELOS Hotbuf Bootstrap ===")
        result = session_bootstrap()

        context_length = len(result.get("context_block", ""))
        mandates_count = len(result.get("mandates", {}))

        print(f"✅ Hotbuf ready: {context_length} chars, {mandates_count} mandates")

        # 성공 상태 반환
        sys.exit(0)

    except Exception as e:
        print(f"❌ Hotbuf bootstrap failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
