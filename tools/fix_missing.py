#!config.PROJECT_HOMEbin/env python3
from modules.core import config
"""
fix_missing.py  (ASCII‑safe)

자동으로 VELOS 구조 오류를 수정합니다.
1) 누락된 스텁 스크립트 생성
2) modules/automation/snapshots 를 디렉터리로 강제
3) vector_cache 내 캐시 파일 플레이스홀더 생성
여러 번 실행해도 안전합니다.
"""

import argparse, datetime as dt, sys
from pathlib import Path

STUBS = {
    "scripts/auto_recovery_agent.py": (
        '"""Auto-recovery agent stub"""\n\n'
        'def main():\n'
        '    print("[Stub] auto_recovery_agent running ...")\n\n'
        'if __name__ == "__main__":\n'
        '    main()\n'
    ),
    "scripts/reflection_agent.py": (
        '"""Reflection agent stub"""\n\n'
        'def main():\n'
        '    print("[Stub] reflection_agent running ...")\n\n'
        'if __name__ == "__main__":\n'
        '    main()\n'
    ),
    "modules/advanced/advanced_rag.py": (
        '"""Advanced RAG engine stub"""\n\n'
        'class AdvancedRAG:\n'
        '    def query(self, text):\n'
        '        return f"[Stub] You asked: {text}"\n\n'
        'if __name__ == "__main__":\n'
        '    print("AdvancedRAG stub ready")\n'
    ),
}

VECTOR_CACHE = [
    "vector_cache/cache_responses.npy",
    "vector_cache/embeddings.npy",
    "vector_cache/local_index.faiss",
]

SNAPSHOTS_DIR = "modules/automation/snapshots"


def create_stubs(root: Path):
    for rel, body in STUBS.items():
        p = root / rel
        if p.exists():
            print(f"[skip] {rel} already exists")
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        print(f"[create] {rel}")


def ensure_snapshots_dir(root: Path):
    tgt = root / SNAPSHOTS_DIR
    if tgt.exists() and tgt.is_file():
        backup = tgt.with_name(
            f"snapshots_old_{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
        )
        tgt.rename(backup)
        print(f"[rename] snapshots file -> {backup.name}")
    if not tgt.exists():
        tgt.mkdir(parents=True)
        print(f"[create] {SNAPSHOTS_DIR}/")
    else:
        print(f"[ok] {SNAPSHOTS_DIR}/ is directory")


def ensure_vector_cache(root: Path):
    (root / "vector_cache").mkdir(exist_ok=True)
    for rel in VECTOR_CACHE:
        f = root / rel
        if not f.exists():
            f.touch()
            print(f"[create] {rel} (placeholder)")
        else:
            print(f"[skip] {rel} exists")


def main():
    ap = argparse.ArgumentParser(description="Fix missing VELOS items.")
    ap.add_argument("--root", default=".", help="Repository root path")
    root = Path(ap.parse_args().root).resolve()

    if not root.exists():
        print(f"Root path {root} not found", file=sys.stderr)
        sys.exit(1)

    create_stubs(root)
    ensure_snapshots_dir(root)
    ensure_vector_cache(root)

    print("\n✅  Done.  Re‑run verify_structure.py to confirm.")


if __name__ == "__main__":
    main()



