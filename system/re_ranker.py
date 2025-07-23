import os
import cohere
from langchain.schema import Document

class ReRanker:
    def __init__(self, api_key=None, model="rerank-v3.5"):
        """
        Cohere Reranker using Cohere Python SDK v5.
        Requires COHERE_API_KEY environment variable or api_key argument.
        """
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("COHERE_API_KEY 환경 변수를 설정해주세요.")
        self.model = model
        # Cohere SDK client
        self.client = cohere.Client(self.api_key)

    def rerank(self, query: str, docs: list[Document], top_n: int = None):
        """
        Rerank documents for the given query.
        :param query: 사용자 쿼리 문자열
        :param docs: langchain.schema.Document 리스트
        :param top_n: 반환할 상위 문서 수 (기본: 전체)
        :return: Cohere RerankResponse 객체 (print()로 결과 확인 가능)
        """
        texts = [doc.page_content for doc in docs]
        # top_n 지정이 없으면 전체 문서 수 사용
        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=texts,
            top_n=top_n or len(texts)
        )
        return response