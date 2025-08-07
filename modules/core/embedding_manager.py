"""
File: core/embedding_manager.py

Description
-----------
- OpenAI 임베딩(text‑embedding‑ada‑002) + FAISS 벡터 검색
- **규칙(rule)** 인덱스 + **문서/메모리** 인덱스를 한 클래스에 통합
- 추가 메서드
    * build_index_from_ndjson()  # 정규화 ND‑JSON → 벡터 인덱스
    * query_similar_docs()       # 자유 텍스트 질의로 메모리 검색
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import openai
import faiss
import numpy as np


class EmbeddingManager:
    """Embeds & searches rules **and** arbitrary memory documents."""

    def __init__(self,
                 rules_path: Optional[Path] = None,
                 model_name: str = "text-embedding-ada-002"):
        self.model_name = model_name

        # ---------- RULE INDEX ----------
        if rules_path:
            self.rules_path = Path(rules_path)
            self._load_rules()
            self.rule_vectors: np.ndarray = self._embed_batch(self.rules)
            self.rule_index = self._build_faiss(self.rule_vectors)
        else:
            self.rules, self.rule_vectors, self.rule_index = [], None, None

        # ---------- DOCUMENT (MEMORY) INDEX ----------
        self.doc_vectors: Optional[np.ndarray] = None
        self.doc_texts: List[str] = []
        self.doc_meta: List[Dict[str, Any]] = []
        self.doc_index: Optional[faiss.Index] = None

    # ------------------------------------------------------------------ #
    #                            Low‑level utils                         #
    # ------------------------------------------------------------------ #
    def _embed(self, text: str) -> np.ndarray:
        resp = openai.embeddings.create(input=text,
                                        model=self.model_name)
        return np.asarray(resp.data[0].embedding, dtype="float32")

    def _embed_batch(self, items: List[dict]) -> np.ndarray:
        texts = [
            itm.get("description") or itm.get("text") or json.dumps(itm, ensure_ascii=False)
            for itm in items
        ]
        return np.stack([self._embed(t) for t in texts])

    @staticmethod
    def _build_faiss(vectors: np.ndarray) -> faiss.Index:
        dim = vectors.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(vectors)
        return index

    # ------------------------------------------------------------------ #
    #                                RULES                               #
    # ------------------------------------------------------------------ #
    def _load_rules(self):
        with open(self.rules_path, encoding='utf-8') as f:
            data = json.load(f)
        self.rules = data if isinstance(data, list) else [data]

    def query_similar_rules(self, context: Dict[str, Any],
                            top_k: int = 5) -> List[Dict[str, Any]]:
        if self.rule_index is None:
            raise RuntimeError("Rule index not initialised")
        ctx_vec = self._embed(json.dumps(context, ensure_ascii=False))
        distances, indices = self.rule_index.search(ctx_vec[np.newaxis, :], top_k)
        return [
            {
                "rule": self.rules[idx],
                "similarity": 1.0 / (1.0 + dist)
            }
            for dist, idx in zip(distances[0], indices[0])
        ]

    # ------------------------------------------------------------------ #
    #                      MEMORY / DOCUMENT  INDEX                      #
    # ------------------------------------------------------------------ #
    def build_index_from_ndjson(self,
                                ndjson_path: str,
                                content_field: str = "text"):
        """Normalised ND‑JSON → 벡터 인덱스 (doc_index)."""
        self.doc_texts.clear()
        self.doc_meta.clear()

        vectors = []
        with open(ndjson_path, encoding="utf-8") as fp:
            for line in fp:
                if not line.strip():
                    continue
                rec = json.loads(line)
                txt = rec.get(content_field, "")
                vectors.append(self._embed(txt))
                self.doc_texts.append(txt)
                self.doc_meta.append(rec)

        if not vectors:
            raise ValueError("No valid records found in ND‑JSON")

        self.doc_vectors = np.stack(vectors)
        self.doc_index = self._build_faiss(self.doc_vectors)

    def query_similar_docs(self, query: str,
                           top_k: int = 5) -> List[Dict[str, Any]]:
        if self.doc_index is None:
            raise RuntimeError("Document index not built yet")
        q_vec = self._embed(query)
        distances, indices = self.doc_index.search(q_vec[np.newaxis, :], top_k)
        return [
            {
                "record": self.doc_meta[idx],
                "similarity": 1.0 / (1.0 + dist)
            }
            for dist, idx in zip(distances[0], indices[0])
        ]
