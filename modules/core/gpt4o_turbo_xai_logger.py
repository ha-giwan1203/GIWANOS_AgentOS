from openai import OpenAI
import os
from dotenv import load_dotenv

env_path = "C:/giwanos/config/.env"
load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")

class GPT4oTurboXAILogger:
    def __init__(self):
        if not api_key:
            raise ValueError("환경변수 OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        self.client = OpenAI(api_key=api_key)

    def log_decision(self, decision, reason):
        try:
            prompt = f"Explain clearly why the decision '{decision}' was made based on the reason '{reason}'."
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are GPT-4o Turbo XAI logger, providing detailed explanations for AI decisions."},
                    {"role": "user", "content": prompt}
                ]
            )
            explanation = response.choices[0].message.content
            print(f"[GPT-4o Turbo XAI] Explanation: {explanation}")
            return explanation
        except Exception as e:
            print(f"🚨 GPT-4o Turbo XAI 호출 중 오류 발생: {e}")
            return f"Error: {e}"
