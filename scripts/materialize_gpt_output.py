# VELOS 운영 철학 선언문: 파일명 고정, 하드코딩 금지, 실행 전 이중검증, 실패는 기록 후 차단
from __future__ import annotations

import json
import os
import pathlib
import sys


def materialize_from_json(data: dict, root: str) -> list[str]:
    wrote = []
    for f in data.get("files", []):
        rel = f["path"].replace("/", os.sep)
        dst = pathlib.Path(root, rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fp:
            fp.write(f["content"])
        wrote.append(str(dst))
    reqs = data.get("requirements", [])
    if reqs:
        req_path = pathlib.Path(root, "requirements.txt")
        existing = []
        if req_path.exists():
            existing = [
                line.strip()
                for line in req_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        merged = sorted(set(existing).union(reqs))
        req_path.write_text("\n".join(merged) + "\n", encoding="utf-8")
    return wrote


def main():
    from modules.report_paths import ROOT
    root = str(ROOT)
    payload = sys.stdin.read().strip()
    if not payload:
        print("No input JSON provided", file=sys.stderr)
        sys.exit(2)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("Invalid JSON input", file=sys.stderr)
        sys.exit(2)
    for p in materialize_from_json(data, root):
        print(f"[write] {p}")


if __name__ == "__main__":
    main()
