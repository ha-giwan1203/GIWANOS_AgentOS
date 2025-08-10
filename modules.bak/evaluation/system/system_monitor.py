# C:/giwanos/evaluation/system/system_monitor.py

import psutil
import shutil

def monitor_performance():
    """CPU, 메모리 사용률을 로깅"""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    return {"cpu_percent": cpu, "memory_percent": mem}

def check_memory_usage(threshold: float = 80.0):
    """메모리 사용률이 threshold 이상이면 경고 문자열 반환"""
    usage = psutil.virtual_memory().percent
    if usage >= threshold:
        return f"메모리 사용률 경고: {usage}% (임계치 {threshold}%)"
    return None

def disk_space_alert(path: str = "C:/giwanos"):
    """디스크 여유공간이 10% 이하이면 경고 문자열 반환"""
    total, used, free = shutil.disk_usage(path)
    free_pct = free / total * 100
    if free_pct <= 10:
        return f"디스크 여유공간 경고: {free_pct:.1f}% 남음"
    return None


