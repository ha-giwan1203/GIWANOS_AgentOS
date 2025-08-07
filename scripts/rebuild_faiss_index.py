import faiss
import numpy as np
import os

INDEX_PATH = r"C:\giwanos\vector_cache\local_index.faiss"
dimension = 1536  # OpenAI embedding dimension

# 새 FAISS 빈 인덱스 생성
index = faiss.IndexFlatL2(dimension)

# 빈 벡터를 추가하여 초기화
dummy_vector = np.zeros((1, dimension), dtype='float32')
index.add(dummy_vector)

# 인덱스 파일 저장
faiss.write_index(index, INDEX_PATH)

print("✅ FAISS 인덱스가 새로 생성되었습니다:", INDEX_PATH)
