

from modules.core import config

import requests
import os
from dotenv import load_dotenv

# .env 파일의 절대 경로를 명시적으로 지정하여 로드
env_path = r'C:\giwanos\configs\.env'
load_dotenv(dotenv_path=env_path)

class InternetSearchModule:
    def __init__(self):
        self.api_key = os.getenv("SEARCH_API_KEY")
        self.cx = os.getenv("CUSTOM_SEARCH_CX")

    def search_web(self, query):
        url = "config.nanwww.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': query
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get('items', [])
            return results[0]['snippet'] if results else '검색 결과 없음'
        else:
            return f"API 호출 오류 발생: {response.status_code}"

    def evaluate_result(self, result):
        confidence = 0.95 if "API 호출 오류" not in result else 0.0
        return {"result": result, "confidence": confidence}

if __name__ == "__main__":
    search_module = InternetSearchModule()

    test_query = "오늘의 뉴스"
    result = search_module.search_web(test_query)
    evaluated_result = search_module.evaluate_result(result)

    print(f"쿼리: {test_query}")
    print(f"검색 결과: {evaluated_result['result']}")
    print(f"결과 신뢰도: {evaluated_result['confidence']}")

    # 환경변수 출력하여 재확인
    print("API 키:", os.getenv("SEARCH_API_KEY"))
    print("CX 값:", os.getenv("CUSTOM_SEARCH_CX"))



