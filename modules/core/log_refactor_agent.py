"""
log_refactor_agent.py

- 반복되는 오류 메시지를 로그 파일에서 감지합니다.
- 오류가 반복 발생한 모듈명을 추출하고 추천 리포트를 생성합니다.
"""

import re
import os
from collections import Counter

LOG_PATH = "C:/giwanos/data/logs/master_loop_execution.log"
OUTPUT_PATH = "C:/giwanos/data/logs/refactor_recommendations.md"

def extract_errors(log_text):
    error_lines = [line for line in log_text.splitlines() if "ERROR" in line or "Traceback" in line]
    return error_lines

def detect_common_errors(error_lines):
    simplified = []
    for line in error_lines:
        mod = re.search(r'in (\w+\.py)', line)
        if mod:
            simplified.append(mod.group(1))
        else:
            simplified.append(line.strip()[:100])  # fallback
    return Counter(simplified)

def generate_report(error_counter):
    report_lines = ["# 🔍 반복 오류 분석 결과 (자동 감지)\n"]
    if not error_counter:
        report_lines.append("- 현재 반복 오류 없음. 👍")
        return "\n".join(report_lines)

    report_lines.append("다음 모듈에서 반복되는 오류가 감지되었습니다:\n")
    for err, count in error_counter.most_common(10):
        report_lines.append(f"- `{err}`: {count}회 발생")
    report_lines.append("\n🚨 해당 모듈의 로직 점검 및 리팩터링을 권장합니다.")
    return "\n".join(report_lines)

def run_refactor_agent():
    if not os.path.exists(LOG_PATH):
        print(f"[❌] 로그 파일 없음: {LOG_PATH}")
        return

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log_text = f.read()

    error_lines = extract_errors(log_text)
    error_counter = detect_common_errors(error_lines)
    report = generate_report(error_counter)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[✅] 리팩터링 추천 리포트 생성 완료 → {OUTPUT_PATH}")

if __name__ == "__main__":
    run_refactor_agent()
