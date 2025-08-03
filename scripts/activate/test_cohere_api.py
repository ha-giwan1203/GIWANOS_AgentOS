echo @"
import requests, os
from dotenv import load_dotenv
load_dotenv('C:/giwanos/.env')

headers = {
    'Authorization': f'Bearer {os.getenv("COHERE_API_KEY")}',
    'Content-Type': 'application/json'
}

data = {
    'text': 'VELOS 시스템은 GPT-4o 기반의 초고도화 AI 시스템으로 사용자 요청을 효율적으로 처리하고 자동화를 지원합니다.',
    'model': 'summarize-medium'
}

response = requests.post('https://api.cohere.ai/summarize', json=data, headers=headers)
print(response.json())
"@ > C:\giwanos\test_cohere_api.py
