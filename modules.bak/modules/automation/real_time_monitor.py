class RealTimeMonitor:
    def detect_anomaly(self, metrics):
        if metrics["cpu_usage"] > 90:
            return True
        return False

    def generate_report(self):
        return "Weekly system health report generated."

