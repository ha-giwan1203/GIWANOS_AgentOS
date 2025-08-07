import faiss
import numpy as np
from dotenv import load_dotenv
import os
from openai import OpenAI

# 환경변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 테스트 문장 3개
texts = [
    "회의에서 받은 피드백을 정리했습니다.",
    "시스템 장애 대응 절차를 개선했습니다.",
    "데이터 백업 방법을 검토했습니다."
]

# 임베딩 생성 함수
def get_embedding(text):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

# FAISS 인덱스 생성
dimension = 1536
index = faiss.IndexFlatL2(dimension)

# 임베딩 추가
embeddings = np.array([get_embedding(text) for text in texts], dtype='float32')
index.add(embeddings)

# 쿼리 임베딩 (유사성 테스트용)
query_text = "팀 회의 피드백 정리"
query_embedding = np.array([get_embedding(query_text)], dtype='float32')

# FAISS로 가장 유사한 항목 검색 (상위 2개)
distances, indices = index.search(query_embedding, k=2)

# 결과 출력
print(f"🔍 쿼리: {query_text}")
print("상위 2개 검색 결과:\n")
for idx, dist in zip(indices[0], distances[0]):
    similarity = 1 / (1 + dist)
    print(f"유사도: {similarity:.3f} | 문장: {texts[idx]}")
