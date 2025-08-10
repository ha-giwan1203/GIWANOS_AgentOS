
# gpt.py (최신 OpenAI API 방식, UTF-8 문제 해결)

from openai import OpenAI

class GPT:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def call(self, prompt, temperature=0.1, model="gpt-4"):
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        content = response.choices[0].message.content
        return content.encode('utf-8').decode('utf-8')  # UTF-8 강제 인코딩 처리


