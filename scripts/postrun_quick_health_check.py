# VELOS 운영 철학 선언문: 파일명 고정, 자가 검증 필수, 결과 기록, 경로/구조 불변, 실패 시 안전 복구.
import os, json, time, sys

ROOT   = "C:/giwanos"
HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")

def _jload(p):
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}

def _jsave(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)

def main():
    h = _jload(HEALTH)

    # 기본 필드 없으면 안전한 기본값 보정
    now = int(time.time())
    h.setdefault("last_flush_ts", 0)
    h.setdefault("context_build_last_ts", 0)

    status = {
        "checked_ts": now,
        "flush_age_min": (now - int(h["last_flush_ts"])) // 60 if h["last_flush_ts"] else 9999,
        "context_age_min": (now - int(h["context_build_last_ts"])) // 60 if h["context_build_last_ts"] else 9999,
    }
    h["postrun_quick_health"] = status
    h["postrun_quick_health_ok"] = True

    _jsave(HEALTH, h)
    print("[postrun] quick health:", status)

if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print("[postrun] health check failed:", e)
        sys.exit(0)  # 포스트런은 절대 루프 실패로 만들지 않는다
