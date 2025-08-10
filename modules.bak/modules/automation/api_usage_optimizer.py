class ApiUsageOptimizer:
    def __init__(self):
        self.call_count = {}

    def can_call_api(self, api_name):
        count = self.call_count.get(api_name, 0)
        return count < 10

    def record_api_call(self, api_name):
        self.call_count[api_name] = self.call_count.get(api_name, 0) + 1

