
import json
import datetime

def generate_chain_of_thought(memory: str) -> str:
    # 아주 단순한 CoT 템플릿 - 향후 확장 가능
    return f"""[생각 시작]
1. 먼저, 기억을 검토한다: "{memory}"
2. 왜 이런 일이 발생했는지 가정한다.
3. 그로부터 배운 점을 정리한다.
4. 향후 대응 방안을 작성한다.
[생각 끝]"""

def test_cot_prompt():
    memory = "회의 때 팀원들이 내가 너무 일방적으로 주도했다는 피드백을 받았다."
    cot = generate_chain_of_thought(memory)
    result = {
        "memory": memory,
        "cot_prompt": cot,
        "timestamp": datetime.datetime.now().isoformat()
    }
    with open("logs/cot_prompt_test_log.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("✅ CoT 생성 완료\n", cot)

if __name__ == "__main__":
    test_cot_prompt()
