import json
import os
from datetime import datetime

log_dir = "logs"
output_file = os.path.join(log_dir, "evaluation_aggregated_log.jsonl")

def read_json_lines(filepath):
    if not os.path.exists(filepath) or os.stat(filepath).st_size == 0:
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        try:
            # 먼저 배열 전체(json array)로 파싱 시도
            arr = json.loads(content)
            if isinstance(arr, list):
                return arr
            else:
                return [arr]
        except Exception:
            # 안 되면 한 줄씩 json.loads()
            f.seek(0)
            result = []
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    result.append(json.loads(s))
                except Exception:
                    continue
            return result

def aggregate_logs():
    aggregated = []

    # Load rag feedback loop logs
    rag_path = os.path.join(log_dir, "loop_evaluation_log.json")
    if os.path.exists(rag_path):
        rag_logs = read_json_lines(rag_path)
        for entry in rag_logs:
            aggregated.append({
                "type": "RAG_FEEDBACK",
                "memory": entry.get("memory"),
                "score": entry.get("evaluation", {}).get("score"),
                "reason": entry.get("evaluation", {}).get("reason"),
                "timestamp": entry.get("timestamp")
            })

    # Load CoT logs
    cot_path = os.path.join(log_dir, "cot_prompt_test_log.json")
    if os.path.exists(cot_path):
        with open(cot_path, "r", encoding="utf-8") as f:
            try:
                cot_entry = json.load(f)
                if isinstance(cot_entry, list):
                    for e in cot_entry:
                        aggregated.append({
                            "type": "COT_PROMPT",
                            "memory": e.get("memory"),
                            "cot_prompt": e.get("cot_prompt"),
                            "timestamp": e.get("timestamp")
                        })
                else:
                    aggregated.append({
                        "type": "COT_PROMPT",
                        "memory": cot_entry.get("memory"),
                        "cot_prompt": cot_entry.get("cot_prompt"),
                        "timestamp": cot_entry.get("timestamp")
                    })
            except Exception as e:
                print(f"[오류] CoT 파일 파싱 중: {e}")

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        for item in aggregated:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ 통합 로그 저장 완료 → {output_file}")

if __name__ == "__main__":
    aggregate_logs()
