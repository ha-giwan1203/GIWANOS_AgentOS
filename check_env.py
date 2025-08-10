# -*- coding: utf-8 -*-
"""
VELOS 환경 점검 스크립트 (로컬 전용)
- C:/giwanos/configs/.env 로드
- 핵심 ENV, 모델, 룸 해시, 캐시 경로, 토큰 길이 점검
- 문제가 있으면 exit code 1로 종료
"""
from __future__ import annotations
import os, sys, json, shutil
from pathlib import Path

BASE = Path("C:/giwanos")
ENV_PATH = BASE / "configs/.env"

def _ok(x): return "✅" if x else "❌"

def main() -> int:
    sys.path.append(str(BASE))
    # .env 로드
    try:
        from dotenv import load_dotenv   # type: ignore
    except Exception:
        print("❌ python-dotenv 미설치. venv에서: pip install python-dotenv")
        return 1

    if not ENV_PATH.exists():
        print(f"❌ .env 없음: {ENV_PATH}")
        return 1

    load_dotenv(str(ENV_PATH))

    # 핵심 키들
    need = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "ROOM_BASE_ID",
        "SLACK_BOT_TOKEN",
        "NOTION_TOKEN",
    ]
    missing = [k for k in need if not os.getenv(k)]
    print(f"ENV 파일: {ENV_PATH}")
    print("필수 키 상태:", {k: _ok(os.getenv(k)) for k in need})

    # 모델 파라미터 호환성 힌트(gpt‑5 계열)
    mdl = (os.getenv("OPENAI_MODEL") or "").lower()
    if mdl.startswith("gpt-5"):
        print("모델:", os.getenv("OPENAI_MODEL"), "(gpt‑5 계열)")
        print("  • max_completion_tokens 사용, temperature 고정(엔진에서 처리됨)")
    else:
        print("모델:", os.getenv("OPENAI_MODEL"))

    # 룸 해시 계산(코드 기준)
    try:
        from modules.core.chat_rooms import base_room_id
        rid = base_room_id()
        print("ROOM(base_room_id):", rid)
        env_room = os.getenv("ROOM_BASE_ID", "")
        if env_room and env_room != rid:
            print(f"⚠️  ROOM_BASE_ID({env_room}) ≠ 코드계산({rid}) → 혼선 주의")
    except Exception as e:
        print("❌ base_room_id 계산 실패:", e)

    # 캐시 경로 권한/공간
    cache = Path(os.getenv("HF_HOME") or "C:/giwanos/vector_cache")
    cache.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(cache).free // (1024**2)
    print(f"캐시 경로: {cache} (잔여 {free} MB)")

    # 토큰 길이 대충 체크
    for k in ["OPENAI_API_KEY", "NOTION_TOKEN", "SLACK_BOT_TOKEN"]:
        v = os.getenv(k, "")
        print(f"{k}: 길이 {len(v)}", "(설정됨)" if v else "(빈 값)")

    # 결과
    if missing:
        print("❌ 누락 키:", ", ".join(missing))
        return 1
    print("✅ 환경 점검 통과")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
