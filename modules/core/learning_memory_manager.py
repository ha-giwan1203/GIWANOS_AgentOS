# VELOS 학습 메모리 관리자 - 리팩터링 완료
# 사용자/시스템 인사이트를 memory에 명확히 구분 저장하고,
# 중복 저장 방지 및 구조 일관성을 유지하며 판단 시 재활용을 가능케 함.

import json
from datetime import datetime
from pathlib import Path

MEMORY_PATH = Path("C:/giwanos/data/memory/learning_memory.json")

class LearningMemoryManager:
    def __init__(self, path=MEMORY_PATH):
        self.path = path
        self.memory = self._load_memory()

    def _load_memory(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "insights" in data:
                        return data
            except Exception:
                pass
        return {"insights": []}

    def _is_duplicate(self, new_entry):
        return any(
            insight.get("insight") == new_entry.get("insight") and
            insight.get("from") == new_entry.get("from")
            for insight in self.memory["insights"][-30:]  # 최근 30개 기준 중복 방지
        )

    def save_insight(self, insight_text, source="system", tags=None):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "from": source,
            "insight": insight_text.strip(),
            "tags": tags or []
        }

        if not self._is_duplicate(entry):
            self.memory["insights"].append(entry)
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self.memory, f, indent=2, ensure_ascii=False)
                print(f"🧠 메모리에 저장됨 → from: {source}, 내용: {insight_text[:40]}...")
            except Exception as e:
                print(f"❌ 메모리 저장 실패: {e}")
        else:
            print(f"⚠️ 중복 인사이트로 저장 생략됨 → '{insight_text[:40]}...'")

    def get_latest(self, count=10, source_filter=None):
        insights = self.memory.get("insights", [])
        if source_filter:
            insights = [i for i in insights if i.get("from") == source_filter]
        return insights[-count:]

    def get_summary(self):
        user_cmds = [i["insight"] for i in self.memory["insights"] if i.get("from") == "user"]
        system_replies = [i["insight"] for i in self.memory["insights"] if i.get("from") == "system"]
        return {
            "total": len(self.memory["insights"]),
            "user_commands": user_cmds[-5:],
            "system_responses": system_replies[-3:]
        }

# ✅ 사용 예시:
# manager = LearningMemoryManager()
# manager.save_insight("Check system health", source="user", tags=["명령", "점검"])
# manager.save_insight("System OK", source="system", tags=["결과"])
# print(manager.get_summary())
