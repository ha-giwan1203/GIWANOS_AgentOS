#!/usr/bin/env python3
"""📄  scripts/normalize_memory.py

다양한 형식의 메모리 파일을 **통일된 ND‑JSON** 레코드로 변환.
(임베딩 파이프라인 직전 단계)
"""

import argparse, json, uuid, yaml
from pathlib import Path
from datetime import datetime

ROOTS = ["data/memory", "data/reflections"]


def parse_dialog(fp):
    obj = json.loads(fp.read_text(encoding="utf-8"))
    for sess in obj.get("sessions", []):
        sid = sess.get("session_id", "")
        for conv in sess.get("conversations", []):
            yield {
                "id": conv.get("id") or str(uuid.uuid4()),
                "text": conv.get("message", ""),
                "ts": conv.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                "meta": {"source": sid,
                         "tags": ["dialog", conv.get("role", "")],
                         "role": conv.get("role", "user")}
            }


def parse_learning(fp):
    obj = json.loads(fp.read_text(encoding="utf-8"))
    for ins in obj.get("insights", []):
        yield {
            "id": ins.get("id") or str(uuid.uuid4()),
            "text": ins.get("insight", ""),
            "ts": ins.get("ts", datetime.utcnow().isoformat() + "Z"),
            "meta": {"source": "learning_memory",
                     "tags": ins.get("tags", ["learning"])}
        }


def parse_reflection(fp):
    obj = json.loads(fp.read_text(encoding="utf-8"))
    yield {
        "id": obj.get("id") or str(uuid.uuid4()),
        "text": obj.get("summary", ""),
        "ts": obj.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "meta": {"source": str(fp), "tags": obj.get("tags", ["reflection"])}
    }


def iter_records():
    for root in ROOTS:
        for fp in Path(root).rglob("*.json"):
            name = fp.name
            if name == "dialog_memory.json":
                yield from parse_dialog(fp)
            elif name == "learning_memory.json":
                yield from parse_learning(fp)
            elif name.startswith("reflection_memory_"):
                yield from parse_reflection(fp)
            else:     # fallback
                obj = json.loads(fp.read_text(encoding="utf-8"))
                yield {"id": str(uuid.uuid4()),
                       "text": json.dumps(obj, ensure_ascii=False),
                       "ts": datetime.utcnow().isoformat() + "Z",
                       "meta": {"source": str(fp), "tags": ["raw"]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None,
                    help="최대 N개까지만 변환(스모크 테스트용)")
    ap.add_argument("--out", required=True,
                    help="출력 ND‑JSON 경로")
    args = ap.parse_args()

    with open(args.out, "w", encoding="utf-8") as out_fp:
        for i, rec in enumerate(iter_records(), 1):
            out_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if args.sample and i >= args.sample:
                break
    print(f"✅  wrote {i} records → {args.out}")


if __name__ == "__main__":
    main()
