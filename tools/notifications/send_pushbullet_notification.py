# =============================================
# VELOS: Pushbullet Notification
# =============================================
from __future__ import annotations
import os, json
from pathlib import Path
from typing import Optional
import requests

LOG_DIR = Path("C:/giwanos/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "notify_pushbullet.log"

def _mask(v: Optional[str]) -> str:
    if not v: return "***"
    return (v[:3] + "***" + v[-3:]) if len(v) > 6 else "***"

def _log(obj: dict):
    try:
        LOG_FILE.write_text("", encoding="utf-8") if not LOG_FILE.exists() else None
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _get_token() -> Optional[str]:
    tok = os.environ.get("PUSHBULLET_TOKEN") or os.environ.get("PUSHBULLET_API_KEY")
    if tok:
        tok = tok.strip().strip("\ufeff")
    return tok

def send_pushbullet_notification(title: str, body: str) -> bool:
    token = _get_token()
    _log({"stage": "init", "token_present": bool(token), "token_mask": _mask(token)})
    if not token:
        print("❌ Pushbullet 토큰이 없습니다.")
        return False

    # 헤더는 latin-1 경계. 제목은 ASCII로 정리.
    ascii_title = (title or "VELOS").encode("ascii", "ignore").decode() or "VELOS"
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {"Access-Token": token, "Content-Type": "application/json"}
    data = {"type": "note", "title": ascii_title, "body": body or ""}

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code == 200:
            _log({"ok": True, "status": r.status_code})
            print("✅ Pushbullet 전송 성공")
            return True
        _log({"ok": False, "status": r.status_code, "resp_len": len(r.text or "")})
        print(f"❌ Pushbullet 전송 실패: {r.status_code}")
        return False
    except Exception as e:
        _log({"ok": False, "exception": str(e)})
        print(f"❌ Pushbullet 예외 발생: {e}")
        return False

if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "VELOS 테스트"
    b = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Pushbullet 통합 점검"
    send_pushbullet_notification(t, b)
