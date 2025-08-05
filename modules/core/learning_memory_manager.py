# 🚀 VELOS(벨로스) 시스템 운영 선언문
# 이 모듈은 VELOS 시스템의 기억 저장을 담당합니다.
# GPT 응답뿐 아니라 사용자 명령도 명확히 분리 저장하며,
# 모든 판단 근거는 메모리에 구조화된 형태로 기록됩니다.

import json
from datetime import datetime
import logging
import os

MEMORY_PATH = "C:/giwanos/data/memory/learning_memory.json"

class LearningMemoryManager:
    @staticmethod
    def save_analysis(analysis_result):
        """
        기존 방식 - GPT 응답만 저장
        """
        try:
            if os.path.exists(MEMORY_PATH):
                with open(MEMORY_PATH, 'r', encoding='utf-8') as mem_file:
                    memory_data = json.load(mem_file)
                    if "insights" not in memory_data:
                        memory_data["insights"] = []
            else:
                memory_data = {"recent_events": [], "insights": [], "performance_metrics": [], "user_behavior": []}

            memory_data["insights"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "from": "system",
                "insight": analysis_result,
                "tags": ["system_response"]
            })

            with open(MEMORY_PATH, 'w', encoding='utf-8') as mem_file:
                json.dump(memory_data, mem_file, indent=4, ensure_ascii=False)

            logging.info("✅ 학습 메모리에 GPT-4o Turbo 분석 결과 저장 완료")

        except Exception as e:
            logging.error(f"❌ 메모리 저장 실패: {e}")

    @staticmethod
    def save_insight(source: str, insight: str, tags: list = None):
        """
        확장 버전 - 사용자 명령 포함, 출처 및 태그 저장
        source: "user" 또는 "system"
        insight: 저장할 내용
        tags: ["명령", "파일명_금지"] 등
        """
        tags = tags or []
        new_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "from": source,
            "insight": insight,
            "tags": tags
        }

        try:
            if os.path.exists(MEMORY_PATH):
                with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        data = {"insights": []}
            else:
                data = {"recent_events": [], "insights": [], "performance_metrics": [], "user_behavior": []}

            data.setdefault("insights", []).append(new_entry)

            with open(MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"✅ 메모리 저장 완료: {source} → {insight[:40]}...")

        except Exception as e:
            print(f"❌ 메모리 저장 실패: {e}")
