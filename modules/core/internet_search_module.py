class InternetSearchModule:
    def search_web(self, query):
        return f"Search result for: {query}"

    def evaluate_result(self, result):
        return {"result": result, "confidence": 0.95}