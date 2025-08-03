
class ContextAwareDecisionEngine:
    def __init__(self, memory_db):
        self.memory_db = memory_db

    def check_memory_availability(self, query):
        return self.memory_db.get(query, None)

    def need_external_search(self, query):
        result = self.check_memory_availability(query)
        return result is None


if __name__ == "__main__":
    import os
    import sys

    class MemoryDB:
        def __init__(self):
            self.db = {
                "내일 날씨 알려줘": "내일은 맑음입니다!",
                "현재 시간은?": "현재 시간은 15시 30분입니다.",
                "오늘 주식 시장 어때?": "코스피는 상승세입니다."
            }

        def get(self, query, default=None):
            return self.db.get(query, default)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("API 키가 설정되지 않았습니다.")
        sys.exit(1)

    engine = ContextAwareDecisionEngine(memory_db=MemoryDB())

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("테스트할 질의를 입력하세요: ")

    if engine.need_external_search(query):
        print(f"[{query}]는 메모리에 없습니다. 외부 검색이 필요합니다.")
    else:
        print(f"[{query}]에 대한 메모리 답변: {engine.check_memory_availability(query)}")
