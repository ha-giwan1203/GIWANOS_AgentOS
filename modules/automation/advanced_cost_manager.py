class AdvancedCostManager:
    def __init__(self, monthly_budget):
        self.monthly_budget = monthly_budget
        self.token_usage = 0
        self.cost_per_token = 0.000015

    def record_token_usage(self, tokens_used):
        self.token_usage += tokens_used

    def current_monthly_cost(self):
        return self.token_usage * self.cost_per_token

    def check_budget(self):
        current_cost = self.current_monthly_cost()
        if current_cost >= self.monthly_budget:
            return "Budget exceeded", current_cost
        elif current_cost >= self.monthly_budget * 0.8:
            return "Budget warning (80%)", current_cost
        else:
            return "Budget normal", current_cost

    def should_limit_api_calls(self):
        status, _ = self.check_budget()
        return status != "Budget normal"