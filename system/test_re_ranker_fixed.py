
from dotenv import load_dotenv
import os
from langchain.schema import Document

# .env 파일에서 COHERE_API_KEY 로드
load_dotenv(dotenv_path=".env")

from re_ranker import ReRanker

# 더미 문서 리스트
docs = [
    Document(page_content="자동차 제조 공정 최적화 방법", metadata={"id": 1}),
    Document(page_content="회고 시스템 확장 방안", metadata={"id": 2}),
    Document(page_content="개인 자동화 회고 시스템 소개", metadata={"id": 3}),
]

rr = ReRanker()
response = rr.rerank("자동화 회고 시스템", docs)
print(response)
