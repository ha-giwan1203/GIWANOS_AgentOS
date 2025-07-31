from gpt4o_turbo_decision_engine import GPT4oTurboDecisionEngine
from gpt4o_turbo_xai_logger import GPT4oTurboXAILogger
from slack_notifier import SlackNotifier
from google_sheets_manager import GoogleSheetsManager

def gpt4o_turbo_integrated_test():
    decision_engine = GPT4oTurboDecisionEngine()
    xai_logger = GPT4oTurboXAILogger()
    slack_notifier = SlackNotifier()
    sheets_manager = GoogleSheetsManager()

    request_analysis = decision_engine.analyze_request("Check system health")
    xai_log = xai_logger.log_decision("System Check", request_analysis)
    slack_result = slack_notifier.send_notification("#general", request_analysis)
    sheets_result = sheets_manager.save_data_to_sheet("System_Health_Report", {"analysis": request_analysis})

    print(request_analysis)
    print(xai_log)
    print(slack_result)
    print(sheets_result)

if __name__ == "__main__":
    gpt4o_turbo_integrated_test()