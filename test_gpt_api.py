
import openai
import os
from dotenv import load_dotenv

load_dotenv("C:/giwanos/config/.env")

openai.api_key = os.getenv("OPENAI_API_KEY")

def test_gpt():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 GIWANOS 시스템입니다."},
                {"role": "user", "content": "GPT 연동 테스트 메시지입니다."}
            ]
        )
        reply = response.choices[0].message.content.strip()
        print(f"[성공] GPT 응답: {reply}")
    except Exception as e:
        print(f"[실패] GPT 연동 오류: {e}")

if __name__ == "__main__":
    test_gpt()
