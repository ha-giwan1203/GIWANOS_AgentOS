# =============================================
# VELOS: Chat Session Restore
# =============================================
from __future__ import annotations
import json, sys
from pathlib import Path

BASE = Path("C:/giwanos")
MEM_FILE = BASE / "data/memory/dialog_memory.json"
SNAP_DIR = BASE / "data/snapshots/chat"

def _read_json(p: Path): return json.loads(p.read_text(encoding="utf-8"))

def restore_from(snapshot: Path) -> Path:
    payload = _read_json(snapshot)
    dialog = payload.get("dialog", {"sessions": []})
    if not isinstance(dialog, dict) or "sessions" not in dialog:
        raise ValueError("잘못된 스냅샷 형식")
    MEM_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEM_FILE.write_text(json.dumps(dialog, ensure_ascii=False, indent=2), encoding="utf-8")
    return MEM_FILE

def main(argv):
    if len(argv) >= 3 and argv[1] == "--from":
        snap = Path(argv[2])
    else:
        latest = (SNAP_DIR / "latest.txt").read_text(encoding="utf-8").strip()
        snap = SNAP_DIR / latest
    out = restore_from(snap)
    print(f"복원 완료: {out}")

if __name__ == "__main__":
    main(sys.argv)
