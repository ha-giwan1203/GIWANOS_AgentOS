
import logging
import psutil
import shutil
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

SNAPSHOT_DIR = 'C:/giwanos/data/snapshots'
CRITICAL_DISK_USAGE_THRESHOLD = 90.0  # 임계 디스크 사용률
CRITICAL_MEMORY_USAGE_THRESHOLD = 90.0  # 임계 메모리 사용률

def system_health_check():
    disk_usage = psutil.disk_usage('/').percent
    memory_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    active_processes = len(psutil.pids())

    health_status = {
        "disk_usage": disk_usage,
        "memory_usage": memory_usage,
        "cpu_usage": cpu_usage,
        "active_processes": active_processes
    }
    
    logging.info(f'System Health: {health_status}')
    return health_status

def critical_condition_handler(health_status):
    if health_status['disk_usage'] > CRITICAL_DISK_USAGE_THRESHOLD:
        logging.warning('Critical disk usage detected, initiating disk cleanup.')
        cleanup_old_snapshots()

    if health_status['memory_usage'] > CRITICAL_MEMORY_USAGE_THRESHOLD:
        logging.warning('Critical memory usage detected, consider terminating unnecessary processes.')

def cleanup_old_snapshots(days_to_keep=1):
    cutoff_date = datetime.now().timestamp() - (days_to_keep * 86400)
    removed_snapshots = 0

    for root, dirs, files in os.walk(SNAPSHOT_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getmtime(file_path) < cutoff_date:
                os.remove(file_path)
                logging.info(f'Removed old snapshot: {file_path}')
                removed_snapshots += 1

    logging.info(f'Total removed snapshots: {removed_snapshots}')

def create_emergency_snapshot():
    snapshot_name = datetime.now().strftime('emergency_snapshot_%Y%m%d%H%M%S')
    snapshot_path = os.path.join(SNAPSHOT_DIR, snapshot_name)
    os.makedirs(snapshot_path, exist_ok=True)
    shutil.copytree('C:/giwanos/core', os.path.join(snapshot_path, 'core'))
    shutil.copytree('C:/giwanos/config', os.path.join(snapshot_path, 'config'))
    logging.info(f'Emergency snapshot created at {snapshot_path}')

def main():
    health_status = system_health_check()
    critical_condition_handler(health_status)

    if health_status['disk_usage'] > CRITICAL_DISK_USAGE_THRESHOLD - 5 or        health_status['memory_usage'] > CRITICAL_MEMORY_USAGE_THRESHOLD - 5:
        logging.info('System nearing critical threshold, creating emergency snapshot.')
        create_emergency_snapshot()

if __name__ == "__main__":
    main()
