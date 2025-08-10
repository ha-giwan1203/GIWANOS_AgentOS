from slack_notifier import SlackNotifier
from google_sheets_manager import GoogleSheetsManager

def slack_google_integration_test():
    slack_notifier = SlackNotifier(api_token="dummy-slack-token")
    sheets_manager = GoogleSheetsManager(credentials_json="dummy-google-credentials.json")

    slack_result = slack_notifier.send_notification("#general", "System operational and healthy.")
    sheets_result = sheets_manager.save_data_to_sheet("System_Report", {"status": "healthy", "uptime": "99.9%"})

    print(slack_result)
    print(sheets_result)

if __name__ == "__main__":
    slack_google_integration_test()

