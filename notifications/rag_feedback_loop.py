#!/usr/bin/env python
import json
import os
import datetime

def evaluate_reflection(reflection: str) -> dict:
    # 더 정교한 평가 기준은 추후 개선
    score = 5 if "왜" in reflection or "때문에" in reflection else 3
    reason = "설명 포함" if score == 5 else "설명 부족"
    return {"score": score, "reason": reason}

def update_prompt_template(current_template: str, evaluation: dict) -> str:
    if evaluation["score"] < 4:
        return "Memory: {memory}\nPlease provide a more detailed reasoning before concluding."
    return current_template

def feedback_loop(memory: str, initial_template: str):
    reflection = initial_template.replace("{memory}", memory)
    evaluation = evaluate_reflection(reflection)
    new_template = update_prompt_template(initial_template, evaluation)

    log = {
        "memory": memory,
        "reflection": reflection,
        "evaluation": evaluation,
        "updated_template": new_template,
        "timestamp": datetime.datetime.now().isoformat()
    }

    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", "loop_evaluation_log.json")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

    print("✅ 평가 완료:", evaluation)
    return new_template

if __name__ == "__main__":
    memory = "오늘 회의에서 내가 말을 너무 많이 했던 것 같아."
    template = "Memory: {memory}\nReflect and provide a helpful suggestion."
    feedback_loop(memory, template)
