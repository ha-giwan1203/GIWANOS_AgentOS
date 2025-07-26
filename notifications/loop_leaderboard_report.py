import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
from datetime import datetime

def generate_report():
    with open("loop_leaderboard.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = [f"# GIWANOS 루프 리더보드 리포트", f"생성 시간: {datetime.now().isoformat()}\n"]
    sorted_users = sorted(data.items(), key=lambda x: x[1]['score'], reverse=True)

    for user, info in sorted_users:
        lines.append(f"- {user}  💠 점수: {info['score']} / 등급: {info['grade']}")
        lines.append(f"  • 루프 완료: {info['loops_completed']}, 성공률: {info['success_rate']}\n")

    filename = f"loop_leaderboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📄 리더보드 리포트 생성 완료: {filename}")

if __name__ == "__main__":
    generate_report()
