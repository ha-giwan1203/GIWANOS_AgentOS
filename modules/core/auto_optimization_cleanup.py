import os
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import json
import shutil
from datetime import datetime
from pathlib import Path

GIWANOS_ROOT = Path("C:/giwanos")

# 판단 룰 최적화 함수
def optimize_judgment_rules():
    rules_path = GIWANOS_ROOT / "core" / "judgment_rules.json"

    if rules_path.exists():
        with open(rules_path, "r", encoding="utf-8") as file:
            rules = json.load(file)

        # 중복 제거 및 정렬 (올바른 필드명으로 수정)
        unique_rules = {json.dumps(rule['conditions'], sort_keys=True): rule for rule in rules}.values()
        optimized_rules = sorted(unique_rules, key=lambda x: x.get('confidence', 0), reverse=True)

        with open(rules_path, "w", encoding="utf-8") as file:
            json.dump(list(optimized_rules), file, indent=4, ensure_ascii=False)

        print(f"Optimized judgment rules at: {now_utc()}")

# 임시 파일 및 불필요 데이터 정리 함수
def cleanup_temp_files():
    temp_dir = GIWANOS_ROOT / ".tmp.driveupload"
    logs_dir = GIWANOS_ROOT / "logs"

    # 임시 디렉터리 삭제
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print(f"Deleted temporary directory at: {temp_dir}")

    # 오래된 로그 파일 정리 (30일 이상된 파일 삭제)
    now = now_utc().timestamp()
    for log_file in logs_dir.glob("*.log"):
        if (now - log_file.stat().st_mtime) > 2592000:  # 30일
            log_file.unlink()
            print(f"Deleted old log file: {log_file}")

# 메인 실행 함수
def main():
    optimize_judgment_rules()
    cleanup_temp_files()

if __name__ == "__main__":
    main()


