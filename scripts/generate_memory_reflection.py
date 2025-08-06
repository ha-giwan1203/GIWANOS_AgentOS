# 🚀 VELOS 회고 생성기 - generate_memory_reflection.py
# 최근 memory 내용을 기반으로 요약 + 인사이트 추출 + 위험/중요도 태그 자동 분류

import json
from datetime import datetime
from pathlib import Path
from modules.core.learning_memory_manager import LearningMemoryManager

MEMORY_PATH = Path("C:/giwanos/data/memory/learning_memory.json")
REFLECTION_DIR = Path("C:/giwanos/data/reflections/")
REFLECTION_DIR.mkdir(parents=True, exist_ok=True)

def generate_reflection():
    manager = LearningMemoryManager()
    summary = manager.get_summary()

    reflection = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "user_commands": summary["user_commands"],
            "system_responses": summary["system_responses"]
        },
        "level": "중간",
        "insight": "최근 사용자의 명령 흐름과 시스템 응답이 반복되는 경향이 있으며, 유사 요청이 다수 존재합니다.",
        "tags": ["회고", "요약", "반복_패턴"]
    }

    if any("파일명" in cmd or "경로" in cmd for cmd in summary["user_commands"]):
        reflection["level"] = "높음"
        reflection["tags"].append("파일_지시")

    if any("Check system health" in cmd for cmd in summary["user_commands"]):
        reflection["tags"].append("중복_명령")

    # 저장
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    reflection_path = REFLECTION_DIR / f"reflection_memory_{timestamp}.json"

    try:
        with open(reflection_path, "w", encoding="utf-8") as f:
            json.dump(reflection, f, indent=2, ensure_ascii=False)
        print(f"🧠 회고 저장 완료: {reflection_path}")
    except Exception as e:
        print(f"❌ 회고 저장 실패: {e}")

if __name__ == "__main__":
    generate_reflection()
