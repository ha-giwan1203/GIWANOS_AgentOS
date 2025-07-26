
paths = [
    r"C:/giwanos/data/logs/master_loop_execution.log",
    r"C:/giwanos/data/reports/system_health.json",
    r"C:/giwanos/memory/loop_evaluation_score.json",
    r"C:/giwanos/agent_logs/judge_agent.log"
]

for path in paths:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            print(f"[✅ 성공] {path} 접근 가능")
    except Exception as e:
        print(f"[❌ 실패] {path} 접근 불가: {e}")
