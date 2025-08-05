# 🚀 VELOS(벨로스) 시스템 운영 선언문
# 이 스크립트는 사용자 명령과 판단 흐름을 반영하여 회고를 생성합니다.
# 단순 키워드가 아닌 태그 기반 분류를 통해 명확한 개선 방향을 도출합니다.

import os
import json
from datetime import datetime

MEMORY_PATH = "C:/giwanos/data/memory/learning_memory.json"
REFLECTION_DIR = "C:/giwanos/data/reflections"

def load_learning_memory(limit=20):
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        insights = data.get("insights", [])
        return insights[-limit:]
    except Exception as e:
        print(f"❌ 메모리 로딩 실패: {e}")
        return []

def generate_summary(memory):
    if not memory:
        return "최근 대화 기록이 없어 회고를 생성할 수 없습니다.", "unknown"

    issues = []
    level = "normal"

    for entry in memory:
        source = entry.get("from", "")
        insight = entry.get("insight", "")
        tags = entry.get("tags", [])

        if source != "user":
            continue  # 사용자 명령만 분석

        if "파일명_금지" in tags:
            issues.append(f"🚨 파일명 변경 금지 명령 감지됨 → '{insight}'")
            level = "critical"
        elif "검증_생략" in tags:
            issues.append(f"⚠️ 검증 없는 파일 제공 지시 감지됨 → '{insight}'")
            if level != "critical":
                level = "warning"
        elif "기억_유지" in tags:
            issues.append(f"📌 기억 유지 요구 → '{insight}'")
        else:
            issues.append(f"✅ 명령 인식됨 → '{insight}'")

    if not issues:
        return "최근 사용자 명령이 없거나 회고 기준에 해당하지 않습니다.", "normal"

    summary = "\n".join(issues)
    return summary, level

def save_reflection(summary, level):
    os.makedirs(REFLECTION_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    filename = f"reflection_memory_{timestamp}.json"
    path = os.path.join(REFLECTION_DIR, filename)

    data = {
        "timestamp": timestamp,
        "category": "memory_reflection",
        "summary": summary,
        "level": level
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
    except Exception as e:
        print(f"❌ 회고 저장 실패: {e}")
        return None

def run_memory_reflection():
    memory = load_learning_memory()
    summary, level = generate_summary(memory)
    return save_reflection(summary, level)

# 실행용 진입점
if __name__ == "__main__":
    path = run_memory_reflection()
    if path:
        print(f"✅ 회고 저장 완료: {path}")
    else:
        print("❌ 회고 저장 실패")
