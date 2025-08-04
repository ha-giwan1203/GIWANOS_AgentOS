from gpt4o_turbo_decision_engine import GPT4oTurboDecisionEngine
from gpt4o_turbo_xai_logger import GPT4oTurboXAILogger
from slack_client import SlackClient

def gpt4o_turbo_integrated_test():
    decision_engine = GPT4oTurboDecisionEngine()
    xai_logger = GPT4oTurboXAILogger()
    slack_client = SlackClient()

    request_analysis = decision_engine.analyze_request("Check system health")
    xai_log = xai_logger.log_decision("System Check", request_analysis)
    slack_result = slack_client.send_message("#general", request_analysis)

    print("Request Analysis:", request_analysis)
    print("XAI Log:", xai_log)
    print("Slack Result:", slack_result)

if __name__ == "__main__":
    gpt4o_turbo_integrated_test()
