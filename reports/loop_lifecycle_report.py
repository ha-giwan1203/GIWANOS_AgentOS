import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime

def generate_lifecycle_report():
    with open("loop_lifecycle_log.json", "r", encoding="utf-8") as f:
        log = json.load(f)

    lines = [f"# 루프 생명주기 리포트", f"생성 시각: {datetime.now().isoformat()}\n"]
    for loop, data in log.items():
        lines.append(f"- {loop}:")
        lines.append(f"  • 현재 상태: {data['status']}")
        lines.append(f"  • 마지막 갱신: {data['last_updated']}")
        lines.append(f"  • 이력: {' → '.join(data['history'])}\n")

    filename = f"loop_lifecycle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📄 생명주기 리포트 생성 완료: {filename}")

if __name__ == "__main__":
    generate_lifecycle_report()
