
class ContextAwareDecisionEngine:
    def __init__(self, memory_db):
        self.memory_db = memory_db

    def check_memory_availability(self, query):
        return self.memory_db.get(query, None)

    def need_external_search(self, query):
        result = self.check_memory_availability(query)
        return result is None

if __name__ == "__main__":
    # 간단한 메모리 데이터베이스 테스트용 딕셔너리 생성
    test_memory_db = {"날씨": "오늘 날씨는 맑습니다."}

    # 엔진 초기화
    decision_engine = ContextAwareDecisionEngine(test_memory_db)

    # 테스트 쿼리
    test_queries = ["날씨", "뉴스"]

    for query in test_queries:
        if decision_engine.need_external_search(query):
            print(f"[{query}] 외부 검색 필요: 메모리에 데이터 없음")
        else:
            print(f"[{query}] 메모리에서 데이터 발견: {decision_engine.check_memory_availability(query)}")


