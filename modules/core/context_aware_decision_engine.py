# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================

import os
import openai
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_gpt_response(prompt: str) -> str:
    try:
        print("🧠 GPT API 호출 중...")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 VELOS 시스템의 판단 에이전트입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=800
        )

        output = response.choices[0].message.content
        print("✅ GPT 응답 완료")
        return output.strip()

    except Exception as e:
        print(f"❌ GPT 호출 실패: {e}")
        return "[GPT 판단 실패 – 예외 발생]"

if __name__ == "__main__":
    result = generate_gpt_response("시스템 상태를 요약해줘")
    print("▶️ GPT 응답:", result)
