import json

def test_load(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"[✅] 로딩 성공: {path}")
            print("데이터:", data[-1])
    except Exception as e:
        print(f"[❌] 로딩 실패: {path}, 오류: {e}")

test_load("C:/giwanos/data/logs/api_cost_log.json")
test_load("C:/giwanos/data/memory/learning_memory.json")


