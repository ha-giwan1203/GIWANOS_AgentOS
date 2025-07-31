class SlackNotifier:
    def __init__(self, api_token):
        self.api_token = api_token

    def send_notification(self, channel, message):
        return f"Notification sent to Slack channel {channel}: {message}"