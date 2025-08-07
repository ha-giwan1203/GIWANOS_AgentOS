import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

try:
    res = client.embeddings.create(input="테스트 문장", model="text-embedding-3-small")
    print("✅ API 키 정상 작동, 임베딩 길이:", len(res.data[0].embedding))
except Exception as e:
    print("❌ API 키 오류 발생:", e)
