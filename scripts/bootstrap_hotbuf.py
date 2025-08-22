#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VELOS Hotbuf Bootstrap Script
핫버퍼 시스템을 초기화하고 세션을 준비합니다.
"""

import sys
import os

# ROOT 경로 설정  
ROOT = os.getenv("VELOS_ROOT", "/workspace")
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
