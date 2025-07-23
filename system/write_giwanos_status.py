# write_giwanos_status.py
import os
import json
import glob
import datetime

# 경로 설정 (필요시 수정)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REFLECTION_DIR = os.path.join(BASE_DIR, "reflections")
BACKUP_DIR = os.path.join(BASE_DIR, "loop_backups")
MEMORY_LOG = os.path.join(BASE_DIR, "memory_log.md")
MEMORY_STATUS = os.path.join(BASE_DIR, "memory_status.json")
EVALUATION_LOG = os.path.join(BASE_DIR, "loop_evaluation_log.json")
NOTION_RESULT_FILE = os.path.join(BASE_DIR, "upload_notion_safe.py")  # Placeholder

# 최신 파일 찾기 함수
def get_latest_file(path, pattern):
    files = glob.glob(os.path.join(path, pattern))
    if not files:
        return None
    latest = max(files, key=os.path.getctime)
    return os.path.basename(latest)

# 백업 파일 요약
def summarize_backups():
    files = glob.glob(os.path.join(BACKUP_DIR, "*.zip"))
    return [os.path.basename(f) for f in sorted(files, reverse=True)[:3]]

# 메모리 상태 확인
def check_memory_status():
    issues = []
    if os.path.exists(MEMORY_LOG):
        with open(MEMORY_LOG, encoding="utf-8") as f:
            for line in f:
                if "Warning" in line or "Error" in line:
                    issues.append(line.strip())
    if os.path.exists(MEMORY_STATUS):
        with open(MEMORY_STATUS, encoding="utf-8") as f:
            status_data = json.load(f)
            if not status_data.get("status_ok", True):
                issues.append("Memory status not OK")
    return issues

# 평가 로그에서 개선 항목 확인 (JSON Lines 형식 대응)
def extract_next_tasks():
    if not os.path.exists(EVALUATION_LOG):
        return []
    tasks = []
    with open(EVALUATION_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                tasks.extend(obj.get("next_tasks", []))
            except json.JSONDecodeError:
                continue
    return tasks

# 요약 저장
def write_summary():
    summary = {
        "generated_at": datetime.datetime.now().isoformat(),
        "latest_pdf": get_latest_file(REFLECTION_DIR, "*.pdf"),
        "latest_md": get_latest_file(REFLECTION_DIR, "*.md"),
        "recent_backups": summarize_backups(),
        "memory_issues": check_memory_status(),
        "next_tasks": extract_next_tasks(),
    }

    with open("giwanos_status_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("✅ GIWANOS 상태 요약 저장 완료: giwanos_status_summary.json")

if __name__ == "__main__":
    write_summary()
