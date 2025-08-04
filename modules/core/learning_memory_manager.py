import json
from datetime import datetime
import logging
from modules.core.error_handler import handle_exception

MEMORY_PATH = "C:/giwanos/memory/learning_memory.json"

def update_learning_memory():
    try:
        with open('C:/giwanos/data/logs/api_cost_log.json', 'r', encoding='utf-8') as f:
            analysis_result = json.load(f)[-1]["analysis_result"]

        with open(MEMORY_PATH, 'r', encoding='utf-8') as mem_file:
            memory_data = json.load(mem_file)

        memory_data["insights"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "insight": analysis_result
        })

        with open(MEMORY_PATH, 'w', encoding='utf-8') as mem_file:
            json.dump(memory_data, mem_file, indent=4, ensure_ascii=False)

        logging.info("✅ 학습 메모리에 GPT-4o Turbo 분석 결과 저장 완료")
    except Exception as e:
        handle_exception(e, context="학습 메모리 업데이트 실패")

if __name__ == "__main__":
    update_learning_memory()
