
class EmergencyRecoveryAgent:
    def diagnose_issue(self, system_status):
        if system_status == "critical":
            return True
        return False

    def perform_recovery(self):
        return "System recovery performed successfully."

    def send_alert(self, channel, message):
        return f"Alert sent via {channel}: {message}"


if __name__ == "__main__":
    import sys

    agent = EmergencyRecoveryAgent()
    
    if len(sys.argv) > 1:
        system_status = sys.argv[1]
    else:
        system_status = "critical"

    if agent.diagnose_issue(system_status):
        recovery_result = agent.perform_recovery()
        alert_result = agent.send_alert("email", "긴급 복구 수행 완료")
        print("진단 결과: 심각한 문제가 감지되었습니다.")
        print(recovery_result)
        print(alert_result)
    else:
        print("진단 결과: 시스템 정상입니다. 복구 불필요.")
