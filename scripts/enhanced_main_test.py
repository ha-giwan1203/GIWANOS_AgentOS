from emergency_recovery_agent import EmergencyRecoveryAgent
from real_time_monitor import RealTimeMonitor

def enhanced_main_test():
    recovery_agent = EmergencyRecoveryAgent()
    monitor = RealTimeMonitor()

    system_status = "critical"
    metrics = {"cpu_usage": 95}

    if recovery_agent.diagnose_issue(system_status):
        recovery_result = recovery_agent.perform_recovery()
        alert_result = recovery_agent.send_alert("SMS", "Critical system issue detected.")
    else:
        recovery_result = "No recovery needed."
        alert_result = "No alert sent."

    if monitor.detect_anomaly(metrics):
        anomaly_report = monitor.generate_report()
    else:
        anomaly_report = "No anomalies detected."

    return recovery_result, alert_result, anomaly_report

if __name__ == "__main__":
    results = enhanced_main_test()
    print(results)

