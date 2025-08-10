# gpt4o_turbo_decision_engine.py 내의 정확한 호출 코드 예시

from openai import OpenAI
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv("C:/giwanos/configs/.env")
api_key = os.getenv("OPENAI_API_KEY")

class GPT4oTurboDecisionEngine:
    def __init__(self):
        self.client = OpenAI(api_key=api_key)

    def analyze_request(self, request):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "GPT-4o Turbo API Call"},
                {"role": "user", "content": request}
            ]
        )

        analysis_result = response.choices[0].message.content

        self.record_api_usage(response.usage, "gpt-4o", analysis_result)
        return analysis_result

    def record_api_usage(self, usage, model_name, analysis_result):
        log_path = "C:/giwanos/data/logs/api_cost_log.json"
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model_name,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": usage.total_tokens * 0.00001,
            "analysis_result": analysis_result
        }

        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    if isinstance(data, dict):
                        data = [data]
                    elif not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        data.append(record)

        with open(log_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)


