from __future__ import annotations
# =============================================
# VELOS: Chat Session Backup
# =============================================

from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic

import json
from pathlib import Path
from typing import Dict, Any

BASE = Path("C:/giwanos")
MEM_FILE = BASE / "data/memory/dialog_memory.json"
JUDGE_IDX = BASE / "data/judgments/judgment_history_index.json"
REPORTS  = BASE / "data/reports"
SNAP_DIR = BASE / "data/snapshots/chat"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

def _now() -> str:
    return now_kst().strftime("%Y%m%d_%H%M%S")

def _read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def _summarize_for_md(dialog: Dict[str, Any]) -> str:
    sessions = dialog.get("sessions", [])
    last = sessions[-1] if sessions else {}
    msg = (last.get("conversations") or [{}])[-1].get("message", "")
    ts  = last.get("created_at", "")
    out = [
        "# VELOS 대화 스냅샷",
        f"- 생성(UTC): {now_utc().isoformat()}Z",
        f"- 세션 수: {len(sessions)}",
        f"- 최근 메시지 타임스탬프: {ts}",
        "",
        "## 최근 메시지",
        "```",
        msg if isinstance(msg, str) else json.dumps(msg, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(out)

def create_snapshot() -> dict:
    dialog = _read_json(MEM_FILE, {"sessions": []})
    judgments = _read_json(JUDGE_IDX, [])
    payload = {
        "meta": {
            "created_utc": now_utc().isoformat() + "Z",
            "created_kst": now_kst().isoformat(),
            "counts": {"sessions": len(dialog.get("sessions", [])), "judgments": len(judgments)}
        },
        "dialog": dialog,
        "judgments": judgments
    }
    ts = _now()
    j = SNAP_DIR / f"chat_snapshot_{ts}.json"
    m = SNAP_DIR / f"chat_snapshot_{ts}.md"
    j.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    m.write_text(_summarize_for_md(dialog), encoding="utf-8")
    (SNAP_DIR / "latest.txt").write_text(j.name, encoding="utf-8")
    return {"json": str(j), "md": str(m)}

if __name__ == "__main__":
    print(create_snapshot())
