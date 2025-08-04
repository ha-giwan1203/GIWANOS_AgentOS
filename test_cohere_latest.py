import requests, os
from dotenv import load_dotenv
load_dotenv('C:/giwanos/.env')

headers = {
    'Authorization': f'Bearer {os.getenv("COHERE_API_KEY")}',
    'Content-Type': 'application/json'
}

data = {
    'text': '''
    VELOS 시스템은 최신 GPT-4o 기술을 기반으로 구축된 고성능 AI 자동화 및 의사결정 지원 시스템입니다. 
    이 시스템은 사용자로부터 입력받은 다양한 자연어 쿼리를 맥락에 맞게 이해하고, 관련된 정보와 데이터를 신속하게 검색하여 
    최적의 결과를 제공하며, 중복 탐색 및 불필요한 연산을 최소화하여 효율성을 극대화합니다.
    또한 시스템이 수행한 모든 작업 결과는 자동으로 기록되어 데이터베이스에 저장되며, 
    필요할 때마다 다양한 보고서 형태로 관리자가 쉽게 확인할 수 있도록 설계되어 있습니다. 
    아울러 자동화된 장애 진단 및 복구 메커니즘을 갖추고 있어 시스템에 문제가 발생할 경우 자체적으로 진단하고 즉시 복구를 시도합니다.
    ''',
    'model': 'command'  # 최신 Cohere 모델 적용
}

response = requests.post('https://api.cohere.ai/summarize', json=data, headers=headers)
print(response.json())
