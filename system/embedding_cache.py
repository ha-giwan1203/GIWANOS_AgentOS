from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings

class EmbeddingCache:
    def __init__(self, persist_directory="vector_cache", collection_name="giwanos_reflection", openai_api_key=None):
        # OPENAI_API_KEY 취득 (인자 우선, 없으면 .env)
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        os.makedirs(persist_directory, exist_ok=True)
        # 벡터 DB 초기화
        self.db = Chroma(
            collection_name=self.collection_name,
            embedding_function=OpenAIEmbeddings(openai_api_key=api_key),
            persist_directory=self.persist_directory
        )

    def add_text(self, text, metadata=None):
        self.db.add_texts([text], metadatas=[metadata or {}])

    def search(self, query, top_k=3):
        return self.db.similarity_search(query, k=top_k)

    def persist(self):
        self.db.persist()