import os
from openai import OpenAI
from dotenv import load_dotenv

# 실제 .env 파일의 정확한 위치를 지정
env_path = "C:/giwanos/config/.env"
load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")

if api_key is None:
    raise ValueError("환경변수 OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

client = OpenAI(api_key=api_key)

def generate_rules():
    prompt = "아래 상황에 대한 판단 규칙을 JSON 형태로 생성하세요: 시스템 실행 중 진단 및 평가 상황."
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    rules = response.choices[0].message.content
    
    with open("C:/giwanos/data/decision_rules.json", "w", encoding="utf-8") as file:
        file.write(rules)

    print("Decision rules generated successfully.")

if __name__ == "__main__":
    generate_rules()
