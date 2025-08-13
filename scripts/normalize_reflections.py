from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from modules.report_paths import ROOT, P
REFLECT = ROOT / r"data\reflections"
OUTIDX = REFLECT / "reflections_index.json"

# 요약에 쓸 후보 필드들(우선순위)
TEXT_FIELDS = (
    "summary",
    "title",
    "message",
    "text",
    "content",
    "insight",
    "log",
    "details",
    "note",
    "body",
)

LEVEL_PATTERNS = [
    ("error", re.compile(r"\b(error|exception|traceback|fail(ed)?|critical)\b", re.I)),
    ("warn", re.compile(r"\b(warn|warning|degraded|retry|timeout|latency)\b", re.I)),
    ("info", re.compile(r".*", re.S)),  # 기본값
]


def _load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _pick_text(d: dict) -> str | None:
    for k in TEXT_FIELDS:
        v = d.get(k)
        if v:
            return str(v)
    # dict 전체에서 문자열 값 아무거나
    for v in d.values():
        if isinstance(v, str) and v.strip():
            return v
    return None


def _one_liner(s: str, limit=140) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _classify(s: str) -> str:
    for lvl, pat in LEVEL_PATTERNS:
        if pat.search(s or ""):
            return lvl
    return "info"


def normalize_file(p: Path) -> dict | None:
    d = _load_json(p)
    if not isinstance(d, dict):
        d = {"raw": d}
    text = _pick_text(d) or p.stem
    d["summary"] = d.get("summary") or _one_liner(text)
    d["level"] = d.get("level") or _classify(text)
    d["source_file"] = p.name
    d["normalized_at"] = datetime.now().isoformat(timespec="seconds")
    # 원본은 보존하고, *_norm.json 으로 출력
    out = p.with_name(p.stem + "_norm.json")
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    # mtime을 최신으로 만들기 위해 한 번 더 씀
    out.touch()
    return {"file": out.name, "title": d["summary"], "level": d["level"]}


def main():
    REFLECT.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(REFLECT.glob("*.json")):
        # 이미 _norm.json 인 파일은 건너뛴다
        if p.name.endswith("_norm.json"):
            continue
        try:
            rec = normalize_file(p)
            if rec:
                items.append(rec)
        except Exception as e:
            items.append({"file": p.name, "title": f"normalize failed: {e}", "level": "warn"})
    # 최신 20개 인덱스
    OUTIDX.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "items": items[-20:],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[OK] normalized {len(items)} reflections, index written:", OUTIDX)


if __name__ == "__main__":
    main()

