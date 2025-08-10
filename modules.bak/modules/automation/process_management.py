
import psutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# CPU 및 메모리 사용량 기준 설정 (조정된 안전한 값)
CPU_USAGE_LIMIT = 85.0  # CPU 사용률 85% 초과 프로세스 종료
MEMORY_USAGE_LIMIT = 1000  # 메모리 사용량 1000MB 초과 프로세스 종료

# 예외 프로세스 지정
EXCLUDE_PROCESSES = ['chrome.exe', 'explorer.exe', 'code.exe', 'python.exe']

def check_and_terminate_processes():
    terminated_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            if proc.info['name'].lower() in EXCLUDE_PROCESSES:
                continue  # 중요 프로세스 보호

            cpu_percent = proc.info['cpu_percent']
            memory_usage_mb = proc.info['memory_info'].rss / (1024 * 1024)

            if cpu_percent > CPU_USAGE_LIMIT or memory_usage_mb > MEMORY_USAGE_LIMIT:
                proc.terminate()
                terminated_processes.append((proc.info['pid'], proc.info['name'], cpu_percent, memory_usage_mb))
                logging.info(f'Terminated process {proc.info["name"]} (PID: {proc.info["pid"]}) CPU: {cpu_percent}%, Memory: {memory_usage_mb:.2f} MB')

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    logging.info(f'Total terminated processes: {len(terminated_processes)}')

def main():
    check_and_terminate_processes()

if __name__ == "__main__":
    main()


