#!/usr/bin/env python3
"""📄 scripts/embed_test.py

정규화된 ND‑JSON 샘플을 읽어 임베딩 → 검색까지 ‘스모크 테스트’.
중첩 JSON을 파싱하여 정확한 필드를 임베딩에 사용 (최종 수정본)
"""

import argparse, itertools, json, os, sys
from openai import OpenAI
import numpy as np
import faiss
import re
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

sys.path.append(os.path.abspath("modules/core"))

def preprocess(text):
    text = re.sub(r"[^가-힣A-Za-z0-9\s]", "", text)
    return text.strip()

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

class EmbeddingManager:
    def __init__(self):
        self.embeddings = []
        self.records = []
        self.dimension = 1536
        self.index = faiss.IndexFlatL2(self.dimension)

    def extract_meaningful_text(self, record):
        text = record.get('text', '')
        try:
            inner_json = json.loads(text)
            meaningful_text = inner_json.get('memory') or inner_json.get('text', '')
        except json.JSONDecodeError:
            meaningful_text = text
        return meaningful_text

    def build_index_from_ndjson(self, ndjson_path):
        with open(ndjson_path, encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                meaningful_text = self.extract_meaningful_text(record)
                embedding = get_embedding(preprocess(meaningful_text))
                self.embeddings.append(embedding)
                self.records.append(record)
        embeddings_array = np.array(self.embeddings, dtype='float32')
        self.index.add(embeddings_array)

    def query_similar_docs(self, query, top_k=3):
        query_embedding = np.array([get_embedding(preprocess(query))], dtype='float32')
        distances, indices = self.index.search(query_embedding, top_k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            similarity = 1 / (1 + dist)
            results.append({
                'similarity': similarity,
                'record': self.records[idx]
            })
        return results

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True, help="normalised ND‑JSON")
    p.add_argument("-n", "--num", type=int, default=10, help="샘플 레코드 수")
    p.add_argument("-q", "--query", default="시스템 헬스 체크 방법?")
    p.add_argument("-k", "--top-k", type=int, default=3)
    args = p.parse_args()

    tmp = "_sample.ndjson"
    with open(args.input, encoding="utf-8") as src, \
         open(tmp, "w", encoding="utf-8") as dst:
        dst.writelines(itertools.islice(src, args.num))

    em = EmbeddingManager()
    em.build_index_from_ndjson(tmp)

    print(f"🔍 쿼리: {args.query}")
    print(f"상위 {args.top_k}개의 검색 결과:\n")

    for r in em.query_similar_docs(args.query, top_k=args.top_k):
        meaningful_text = em.extract_meaningful_text(r['record'])
        print(f"{r['similarity']:.3f} | {meaningful_text[:80]}...")

    os.remove(tmp)
    print("✅ smoke test complete")

if __name__ == "__main__":
    main()
