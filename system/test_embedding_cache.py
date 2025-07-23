import os, sys

# 현재 스크립트가 있는 C:\giwanos를 패키지 경로로 추가
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from giwanos.vector_store.embedding_cache import EmbeddingCache

ec = EmbeddingCache()
ec.add_text("회고 시스템을 자동화하면 시간을 절약할 수 있다.", metadata={"source": "manual"})
results = ec.search("자동화된 회고 시스템의 장점은?")
for r in results:
    print("🧠", r.page_content)
ec.persist()