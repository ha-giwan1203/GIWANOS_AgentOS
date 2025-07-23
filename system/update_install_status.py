import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
import sys
from datetime import datetime

STATUS_FILE = "install_status.json"

def update_status(loop_name):
    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        status = json.load(f)

    if "루프 실행 상태" not in status["status"]:
        print("루프 실행 상태 구조가 없습니다.")
        return

    if loop_name not in status["status"]["루프 실행 상태"]:
        print(f"[오류] 지정한 루프 '{loop_name}'은 존재하지 않습니다.")
        return

    status["status"]["루프 실행 상태"][loop_name]["완료"] = True
    status["status"]["루프 실행 상태"][loop_name]["완료시간"] = datetime.now().isoformat()

    # 설치 완료 여부 조건 확인
    all_done = all(loop["완료"] for loop in status["status"]["루프 실행 상태"].values())
    status["status"]["설치 완료 여부"] = all_done

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    print(f"[성공] '{loop_name}' 루프 실행 완료로 기록되었습니다.")
    if all_done:
        print("🎉 모든 루프 실행 완료! 설치가 완료되었습니다.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python update_install_status.py '루프명'")
        print("예시 루프명: 정리기 / 판단 루프 / 회고 루프 / 전송 루프 / 통합 실행기")
    else:
        update_status(sys.argv[1])
