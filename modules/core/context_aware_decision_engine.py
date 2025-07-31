class ContextAwareDecisionEngine:
    def __init__(self, memory_db):
        self.memory_db = memory_db

    def check_memory_availability(self, query):
        return self.memory_db.get(query, None)

    def need_external_search(self, query):
        result = self.check_memory_availability(query)
        return result is None