
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv('C:\\giwanos\\configs\\.env')

# OPENAI API 키 로드 확인
print("OpenAI API Key:", os.getenv("OPENAI_API_KEY"))

# GitHub, Notion 키 로드 확인
print("GitHub Token:", os.getenv("GITHUB_TOKEN"))
print("Notion Token:", os.getenv("NOTION_TOKEN"))
