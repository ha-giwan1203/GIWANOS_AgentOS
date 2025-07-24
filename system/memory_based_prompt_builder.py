import os
import json
import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI

# 1. .env에서 API 키 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경변수를 확인하세요.")
    
# 2. OpenAI 클라이언트 초기화 (v1+ 방식)
client = OpenAI(api_key=api_key)

class MemoryRetriever:
    """
    과거 회고 로그(텍스트)를 기반으로 벡터 검색을 수행해 상위 K건의 문서를 반환합니다.
    index_path 디렉터리 안에는 다음 파일이 있어야 합니다:
      - index.faiss : FAISS 인덱스 파일
      - docs.json    : 인덱스에 매핑된 문서(문자열) 리스트(JSON 배열)
    """
    def __init__(self, index_path: str, embedding_model: str = 'text-embedding-ada-002'):
        self.index_file = os.path.join(index_path, 'index.faiss')
        self.docs_file  = os.path.join(index_path, 'docs.json')
        self.embedding_model = embedding_model

        if not os.path.exists(self.index_file):
            raise FileNotFoundError(f"FAISS 인덱스 파일이 없습니다: {self.index_file}")
        if not os.path.exists(self.docs_file):
            raise FileNotFoundError(f"docs.json 파일이 없습니다: {self.docs_file}")

        # FAISS 인덱스 & 문서 리스트 로드
        self.index = faiss.read_index(self.index_file)
        with open(self.docs_file, 'r', encoding='utf-8') as f:
            self.docs = json.load(f)

        if len(self.docs) != self.index.ntotal:
            raise ValueError("docs.json의 문서 수와 FAISS 인덱스 벡터 수 불일치")

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        OpenAI Embedding API(v1+)를 호출해 numpy 배열로 반환
        """
        resp = client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        emb = resp.data[0].embedding
        return np.array(emb, dtype='float32').reshape(1, -1)

    def get_relevant_docs(self, query: str, top_k: int = 5) -> list[str]:
        """
        query: 사용자 요청
        top_k: 반환할 문서 개수
        """
        # 1) 쿼리 임베딩 생성
        q_emb = self._get_embedding(query)
        # 2) FAISS 검색
        distances, indices = self.index.search(q_emb, top_k)
        # 3) 매핑된 문서 반환
        return [ self.docs[idx] for idx in indices[0] if idx < len(self.docs) ]
