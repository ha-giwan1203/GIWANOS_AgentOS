from resource_monitor import ResourceMonitor

def resource_monitor_test():
    monitor = ResourceMonitor(cpu_threshold=90, memory_threshold=90, disk_threshold=90)

    test_case_1 = monitor.check_resources(cpu_usage=80, memory_usage=80, disk_usage=80)
    test_case_2 = monitor.check_resources(cpu_usage=95, memory_usage=95, disk_usage=95)

    print({"test_case_normal": test_case_1, "test_case_warning": test_case_2})

if __name__ == "__main__":
    resource_monitor_test()

