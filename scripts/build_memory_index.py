"""
VELOS 기억을 벡터화하여 FAISS 인덱스와 메타데이터(JSON)를 생성합니다.
"""

import argparse, glob, hashlib, json, os, sys, time
from pathlib import Path
from typing import Iterable, List, Dict
import faiss, numpy as np
from sentence_transformers import SentenceTransformer

GIWANOS_ROOT = str(Path(__file__).resolve().parents[1])
if GIWANOS_ROOT not in sys.path:
    sys.path.append(GIWANOS_ROOT)

MEMORY_PATHS = [
    "C:/giwanos/data/memory/learning_memory.json",
    "C:/giwanos/data/reflections",
]
INDEX_PATH = "C:/giwanos/vector_cache/local_index.faiss"
EMB_PATH = "C:/giwanos/vector_cache/embeddings.json"
MODEL_NAME = "all-MiniLM-L6-v2"

def _iter_records() -> Iterable[Dict]:
    for p in MEMORY_PATHS:
        if os.path.isfile(p):
            try:
                data = json.load(open(p, encoding="utf8"))
                yield from data if isinstance(data, list) else [data]
            except Exception as e:
                print(f"[WARN] {p} 로드 실패: {e}")
        else:
            for fp in glob.glob(os.path.join(p, "*.json")):
                try:
                    data = json.load(open(fp, encoding="utf8"))
                    yield from data if isinstance(data, list) else [data]
                except Exception as e:
                    print(f"[WARN] {fp} 로드 실패: {e}")

def extract_text(record: dict) -> str:
    if "insight" in record:
        return record["insight"]
    elif "text" in record:
        try:
            inner = json.loads(record["text"])
            return inner.get("memory") or inner.get("text", "")
        except json.JSONDecodeError:
            return record["text"]
    return ""

def _dedup_by_hash(texts: List[str], records: List[Dict], old_meta: List[Dict]) -> tuple:
    old_hash = {hashlib.md5(r["text"].encode()).hexdigest() for r in old_meta}
    new_texts, new_records = [], []
    for t, r in zip(texts, records):
        if hashlib.md5(t.encode()).hexdigest() not in old_hash:
            new_texts.append(t)
            new_records.append({"id": r.get("id", ""), "text": t, "tags": r.get("tags", []), "source": r.get("source", "unknown")})
    return new_texts, new_records

def build_index(incremental: bool = False) -> None:
    model = SentenceTransformer(MODEL_NAME)
    records = list(_iter_records())

    texts_records = [(extract_text(r), r) for r in records if extract_text(r).strip()]
    if not texts_records:
        print("⚠️  유효한 레코드가 없습니다. 종료.")
        return

    texts, records = zip(*texts_records)

    if incremental and os.path.exists(EMB_PATH):
        old_meta = json.load(open(EMB_PATH, encoding="utf8"))
        texts, records = _dedup_by_hash(texts, records, old_meta)
        if not texts:
            print("ℹ️  새로운 레코드가 없습니다.")
            return

    emb = model.encode(texts, show_progress_bar=True).astype("float32")
    faiss.normalize_L2(emb)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)

    Path(INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    json.dump(records, open(EMB_PATH, "w", encoding="utf8"), ensure_ascii=False, indent=2)
    print(f"[build_memory_index] 완료 ({len(records)}개 레코드)")

def _self_test() -> None:
    assert os.path.exists(INDEX_PATH), "INDEX_PATH 미생성"
    assert os.path.exists(EMB_PATH), "EMB_PATH 미생성"
    idx = faiss.read_index(INDEX_PATH)
    meta = json.load(open(EMB_PATH, encoding="utf8"))
    assert idx.ntotal == len(meta), "인덱스/메타 크기 불일치"
    print("[build_memory_index] self-test OK", idx.ntotal, "vectors")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--inc", action="store_true", help="증분 갱신")
    args = ap.parse_args()
    try:
        build_index(incremental=args.inc)
        _self_test()
    except Exception as e:
        print(f"[오류] {e}")


