class GoogleSheetsManager:
    def __init__(self, credentials_json):
        self.credentials_json = credentials_json

    def save_data_to_sheet(self, sheet_name, data):
        return f"Data saved to Google Sheet {sheet_name}: {data}"