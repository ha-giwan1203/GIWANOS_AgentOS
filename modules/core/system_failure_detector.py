
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import logging
import json
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)

LOG_FILE_PATH = "C:/giwanos/data/logs/master_loop_execution.log"
HEALTH_FILE_PATH = "C:/giwanos/data/reports/system_health.json"
FAILURE_FLAG_PATH = "C:/giwanos/data/logs/failure_detected.flag"

def load_system_health():
    try:
        with open(HEALTH_FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"시스템 상태 파일 로드 실패: {e}")
        return {"status": "unknown"}

def detect_failure():
    system_health = load_system_health()
    failure_detected = False

    if system_health.get("status") != "모든 시스템이 정상적으로 작동합니다.":
        logging.warning("⚠️ 비정상적인 시스템 상태 감지됨!")
        failure_detected = True

    if failure_detected:
        with open(FAILURE_FLAG_PATH, 'w', encoding='utf-8') as flag_file:
            flag_file.write(f"Failure detected at {now_utc().isoformat()}")
        logging.info("🚨 장애 감지 플래그가 생성되었습니다.")
    else:
        logging.info("✅ 시스템 상태 정상. 장애 미감지.")

if __name__ == "__main__":
    detect_failure()



