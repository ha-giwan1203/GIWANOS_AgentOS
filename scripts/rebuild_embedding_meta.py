import numpy as np
import os

EMB_PATH = r"C:\giwanos\vector_cache\embeddings.npy"

# 초기 더미 메타데이터 생성
dummy_meta = np.array([{"id": "dummy_vector", "description": "초기화용 더미 데이터"}])

# npy 파일로 저장
np.save(EMB_PATH, dummy_meta, allow_pickle=True)

print("✅ 임베딩 메타데이터가 정상적으로 초기화되었습니다:", EMB_PATH)


