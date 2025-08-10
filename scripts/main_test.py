from context_aware_decision_engine import ContextAwareDecisionEngine
from internet_search_module import InternetSearchModule
from tool_manager import ToolManager
from api_usage_optimizer import ApiUsageOptimizer
from xai_logger import XAILogger

def main_test():
    memory_db = {"hello": "Hi there!"}
    context_engine = ContextAwareDecisionEngine(memory_db)
    search_module = InternetSearchModule()
    tool_manager = ToolManager()
    api_optimizer = ApiUsageOptimizer()
    logger = XAILogger()

    query = "new information request"
    if context_engine.need_external_search(query):
        if api_optimizer.can_call_api("internet_search"):
            result = search_module.search_web(query)
            evaluated = search_module.evaluate_result(result)
            logger.log_decision("External Search", evaluated)
            api_optimizer.record_api_call("internet_search")
        else:
            logger.log_decision("Search Skipped", "API Call Limit Reached")
    else:
        logger.log_decision("Internal Memory", "Data Found in Memory")

if __name__ == "__main__":
    main_test()

