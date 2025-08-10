from modules.automation.scheduling.system_health_logger import current_stats

def test_current_stats_keys():
    stats = current_stats()
    assert {"cpu_percent", "memory_percent", "disk_percent"} <= stats.keys()

def test_current_stats_range():
    stats = current_stats()
    assert 0 <= stats["cpu_percent"] <= 100
    assert 0 <= stats["memory_percent"] <= 100
    assert 0 <= stats["disk_percent"] <= 100


