from advanced_cost_manager import AdvancedCostManager
from query_cache import QueryCache

def advanced_cost_management_test():
    cost_manager = AdvancedCostManager(monthly_budget=50)
    cache = QueryCache()

    query = "latest news"
    cached_response = cache.get_cached_response(query)

    if cached_response:
        response = cached_response
        api_call_made = False
    else:
        response = "Fetched from GPT-4o API"
        tokens_used = 2000
        cost_manager.record_token_usage(tokens_used)
        cache.cache_response(query, response)
        api_call_made = True

    budget_status, current_cost = cost_manager.check_budget()
    limit_calls = cost_manager.should_limit_api_calls()

    print({
        "response": response,
        "api_call_made": api_call_made,
        "budget_status": budget_status,
        "current_cost": current_cost,
        "limit_calls": limit_calls
    })

if __name__ == "__main__":
    advanced_cost_management_test()

