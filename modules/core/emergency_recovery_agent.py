class EmergencyRecoveryAgent:
    def diagnose_issue(self, system_status):
        if system_status == "critical":
            return True
        return False

    def perform_recovery(self):
        return "System recovery performed successfully."

    def send_alert(self, channel, message):
        return f"Alert sent via {channel}: {message}"