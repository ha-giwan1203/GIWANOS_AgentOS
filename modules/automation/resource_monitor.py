class ResourceMonitor:
    def __init__(self, cpu_threshold=90, memory_threshold=90, disk_threshold=90):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold

    def check_resources(self, cpu_usage, memory_usage, disk_usage):
        alerts = []
        if cpu_usage > self.cpu_threshold:
            alerts.append(f"CPU 사용률 경고: 현재 {cpu_usage}%")
        if memory_usage > self.memory_threshold:
            alerts.append(f"메모리 사용률 경고: 현재 {memory_usage}%")
        if disk_usage > self.disk_threshold:
            alerts.append(f"디스크 사용률 경고: 현재 {disk_usage}%")
        
        if not alerts:
            return "자원 사용률 정상 범위 내"
        return alerts