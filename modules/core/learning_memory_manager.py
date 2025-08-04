import json
from datetime import datetime
import logging
from modules.core.error_handler import handle_exception

# ✅ 올바른 실제 경로로 수정
MEMORY_PATH = "C:/giwanos/data/memory/learning_memory.json"

class LearningMemoryManager:
    @staticmethod
    def save_analysis(analysis_result):
        try:
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
