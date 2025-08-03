"""
File: C:/giwanos/core/embedding_manager.py

설명:
- OpenAI Embeddings 및 FAISS를 이용한 규칙과 컨텍스트 텍스트 임베딩 생성/검색 모듈
- judgment_rules.json에서 규칙을 로드하여 벡터 인덱스 생성
- 컨텍스트 임베딩을 통해 유사한 규칙을 검색하여 추천
- Updated for openai>=1.0.0 API: use openai.embeddings.create
"""

import os
import json
from pathlib import Path

import openai
import faiss
import numpy as np

class EmbeddingManager:
    def __init__(self, rules_path: Path):
        self.rules_path = Path(rules_path)
        self._load_rules()
        self._build_index()

    def _load_rules(self):
        with open(self.rules_path, encoding='utf-8') as f:
            data = json.load(f)
        # Ensure list of rules
        self.rules = data if isinstance(data, list) else [data]

    def embed_text(self, text: str) -> np.ndarray:
        # OpenAI Embedding API 호출 (v1+)
        resp = openai.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embedding = resp.data[0].embedding
        return np.array(embedding, dtype="float32")

    def _build_index(self):
        # Generate embeddings for each rule
        self.vectors = []
        for rule in self.rules:
            text = rule.get("description", "") + " " + json.dumps(rule.get("conditions", {}), ensure_ascii=False)
            vec = self.embed_text(text)
            self.vectors.append(vec)
        if not self.vectors:
            raise ValueError("No rules to index.")
        self.vectors = np.stack(self.vectors)

        # Build FAISS index
        dim = self.vectors.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.vectors)

    def query_similar_rules(self, context: dict, top_k: int = 5) -> list:
        # Embed context dict as text
        ctx_text = json.dumps(context, ensure_ascii=False)
        ctx_vec = self.embed_text(ctx_text)
        # Search index
        distances, indices = self.index.search(np.expand_dims(ctx_vec, 0), top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            rule = self.rules[idx]
            # Convert L2 distance to similarity score
            similarity = 1.0 / (1.0 + dist)
            results.append({"rule": rule, "similarity": similarity})
        return results
