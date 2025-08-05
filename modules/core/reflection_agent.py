from datetime import datetime
import json
import os

# VELOS 구조 기반으로 고정된 경로 사용
REFLECTION_DIR = "C:/giwanos/data/reflections"
SYSTEM_HEALTH_PATH = "C:/giwanos/data/logs/system_health.json"

def generate_reflection():
    def load_recent_health_logs(limit=5):
        try:
            with open(SYSTEM_HEALTH_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
            return logs[-limit:] if isinstance(logs, list) else []
        except Exception as e:
            return []

    def analyze_system(logs):
        if not logs:
            return "❓ 시스템 로그 없음", "unknown"

        cpu_avg = sum(x.get("cpu_percent", 0) for x in logs) / len(logs)
        mem_avg = sum(x.get("memory_percent", 0) for x in logs) / len(logs)
        disk_avg = sum(x.get("disk_percent", 0) for x in logs) / len(logs)

        summary_lines = []
        level = "normal"

        if cpu_avg > 80:
            summary_lines.append(f"⚠️ 평균 CPU 사용률이 {cpu_avg:.1f}%로 높습니다.")
            level = "warning"
        else:
            summary_lines.append(f"✅ 평균 CPU 사용률: {cpu_avg:.1f}%")

        if mem_avg > 80:
            summary_lines.append(f"⚠️ 평균 메모리 사용률이 {mem_avg:.1f}%로 높습니다.")
            level = "warning"
        else:
            summary_lines.append(f"✅ 평균 메모리 사용률: {mem_avg:.1f}%")

        if disk_avg > 90:
            summary_lines.append(f"🚨 디스크 사용률이 {disk_avg:.1f}%로 매우 높습니다.")
            level = "critical"
        else:
            summary_lines.append(f"✅ 디스크 사용률: {disk_avg:.1f}%")

        return "\n".join(summary_lines), level

    def save_reflection(summary, level):
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        filename = f"reflection_{timestamp}.json"
        path = os.path.join(REFLECTION_DIR, filename)
        os.makedirs(REFLECTION_DIR, exist_ok=True)
        data = {
            "timestamp": timestamp,
            "category": "system_reflection",
            "summary": summary,
            "level": level
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    logs = load_recent_health_logs()
    summary, level = analyze_system(logs)
    return save_reflection(summary, level)

# ✅ 마스터 루프 호환성 유지용 alias
run_reflection = generate_reflection
