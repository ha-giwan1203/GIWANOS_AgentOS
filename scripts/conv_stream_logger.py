# [ACTIVE] VELOS 대화 스트림 로거 - 대화 로깅 시스템
import json
import os
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(os.getenv("VELOS_ROOT", "/home/user/webapp"))
OUT = ROOT / "data" / "session"
OUT.mkdir(parents=True, exist_ok=True)
cur = OUT / f"chat_{datetime.now().strftime('%Y%m%d')}.jsonl"


def write(role, content, tags=None, session_id=None):
    rec = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "role": role,
        "content": content,
        "tags": tags or [],
        "session": session_id or "default",
    }
    cur.write_text("", encoding="utf-8", errors="ignore") if not cur.exists() else None
    with cur.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    # 예시: 테스트용 더미 입력
    write("user", "이건 테스트 메시지")
    write("assistant", "테스트 응답입니다.")
