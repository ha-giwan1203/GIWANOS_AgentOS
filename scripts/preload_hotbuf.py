#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import get_velos_root, get_data_path, get_config_path, get_db_path
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root(): return "C:/giwanos"
    def get_data_path(*parts): return os.path.join("C:/giwanos", "data", *parts)
    def get_config_path(*parts): return os.path.join("C:/giwanos", "configs", *parts)
    def get_db_path(): return "C:/giwanos/data/memory/velos.db"

"""
VELOS Hotbuf Preload Script
세션 핫버퍼를 미리 생성하고 상태를 확인합니다.
"""

import sys
import os
import json

# ROOT 경로 설정
ROOT = get_velos_root() if "get_velos_root" in locals() else "C:/giwanos"
if ROOT not in sys.path:
    sys.path.append(ROOT)

def main():
    try:
        from modules.core.session_memory_boot import session_bootstrap

        # 세션 핫버퍼 미리 생성(없거나 만료 시 자동 재생성)
        out = session_bootstrap()

        # 상태 출력
        print("[preload] hotbuf.created_ts:", out.get("hotbuf_created_ts"))
        print("[preload] mandates:", json.dumps(out.get("mandates", {}), ensure_ascii=False))

        # 컨텍스트 헤드 출력
        context_block = out.get("context_block", "")
        context_lines = context_block.splitlines()
        context_head = "\n".join(context_lines[:4])
        print("[preload] context_head:", context_head)

        # 성공 상태 반환
        sys.exit(0)

    except Exception as e:
        print(f"[ERROR] 핫버퍼 미리 생성 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
