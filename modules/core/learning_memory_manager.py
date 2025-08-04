import json
import logging
from modules.core.error_handler import handle_exception

MEMORY_PATH = "C:/giwanos/memory/learning_memory.json"

def save_learning_memory(memory_data):
    try:
        with open(MEMORY_PATH, 'w', encoding='utf-8') as file:
            json.dump(memory_data, file, indent=4, ensure_ascii=False)
        logging.info("✅ 학습 메모리 저장 성공")
    except (IOError, TypeError, json.JSONDecodeError) as e:
        handle_exception(e, context="학습 메모리 저장 실패")
