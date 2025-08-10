# -*- coding: utf-8 -*-
"""
VELOS 의미검색 모듈 (경량 안정판)
- ENV만으로 제어
- 인덱스 없이 on-the-fly 검색(소규모 전제)
"""

from __future__ import annotations
import os, json
from pathlib import Path
from typing import List, Dict, Tuple

# 캐시 폴더: 프로젝트 안으로 통일(ENV 우선)
os.environ.setdefault("HF_HOME", r"C:\giwanos\.hf")
os.environ.setdefault("TRANSFORMERS_CACHE", r"C:\giwanos\.hf\transformers")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"C:\giwanos\.hf\hub")

EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
LEARNING_MEMORY = Path(os.getenv("LEARNING_MEMORY", r"C:\giwanos\data\memory\learning_memory.json"))

_model = None

def _get_model():
    """SentenceTransformer 지연 로딩"""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
    return _model

def _load_insights(max_items: int = 5000) -> List[Dict]:
    if not LEARNING_MEMORY.exists():
        return []
    try:
        data = json.loads(LEARNING_MEMORY.read_text(encoding="utf-8"))
        items = data.get("insights", [])
        return items[-max_items:]
    except Exception:
        return []

def _to_corpus(items: List[Dict]) -> Tuple[List[str], List[Dict]]:
    texts, rows = [], []
    for it in items:
        t = it.get("insight") or it.get("text")
        if not t:
            continue
        texts.append(t)
        rows.append(it)
    return texts, rows

def search(query: str, k: int = 5) -> List[Dict]:
    """메모리에서 의미 유사 top‑k 반환."""
    items = _load_insights()
    if not items:
        return []

    texts, rows = _to_corpus(items)

    model = _get_model()
    q_vec = model.encode([query], normalize_embeddings=True)
    c_vec = model.encode(texts, normalize_embeddings=True)

    import numpy as np
    sims = (c_vec @ q_vec.T).squeeze()  # (N,)
    idx = np.argsort(-sims)[:max(1, k)]

    out: List[Dict] = []
    for i in idx:
        r = dict(rows[int(i)])
        r["score"] = float(sims[int(i)])
        out.append(r)
    return out
