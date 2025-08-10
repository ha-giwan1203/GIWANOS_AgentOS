
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("C:/giwanos/config/.env")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def generate_examples():
    prompt = "시스템 운영 중 발생할 수 있는 다양한 상황(예: CPU 과부하, 메모리 부족, 디스크 용량 부족 등)과 그에 대한 대응방법을 구체적이고 다양한 예제로 작성하세요. JSON 형식으로 반환하세요."
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    examples = response.choices[0].message.content
    with open("C:/giwanos/data/rag_decision_examples.json", "w", encoding="utf-8") as file:
        file.write(examples)

    print("RAG decision examples generated successfully.")

if __name__ == "__main__":
    generate_examples()


