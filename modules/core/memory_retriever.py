"""
VELOS 메모리 검색 모듈
"""

import os, threading, json, sys
import faiss, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

GIWANOS_ROOT = str(Path(__file__).resolve().parents[2])
if GIWANOS_ROOT not in sys.path:
    sys.path.append(GIWANOS_ROOT)

INDEX_PATH = r"C:\giwanos\vector_cache\local_index.faiss"
EMB_PATH = r"C:\giwanos\vector_cache\embeddings.json"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5

_model = SentenceTransformer(MODEL_NAME)
_index_lock = threading.Lock()

def _load_index():
    if not (os.path.exists(INDEX_PATH) and os.path.exists(EMB_PATH)):
        raise FileNotFoundError("인덱스 또는 메타 데이터가 없습니다.")
    return faiss.read_index(INDEX_PATH), json.load(open(EMB_PATH, encoding="utf8"))

_index, _meta = _load_index()

def _to_dict(obj: dict):
    return {
        "from": obj.get("source", "unknown"),
        "insight": obj.get("text", "데이터 없음"),
        "tags": obj.get("tags", [])
    }

def search(query: str, k: int = TOP_K):
    query = query.strip()
    if not query:
        return []

    vec = _model.encode([query]).astype("float32")
    faiss.normalize_L2(vec)

    with _index_lock:
        _, idx = _index.search(vec, k)

    results = [_to_dict(_meta[i]) for i in idx[0] if i != -1]
    return results

def _self_test():
    res = search("파일명 바꾸지 마", 3)
    assert res, "검색 결과 없음"
    for r in res:
        assert {"from", "insight", "tags"}.issubset(r), "필드 누락"
    print("[memory_retriever] self-test passed:", len(res), "results")

if __name__ == "__main__":
    _self_test()
