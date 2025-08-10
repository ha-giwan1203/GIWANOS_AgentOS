
import threading
import time

class ToolManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.shared_memory = {}

    def execute_tool(self, tool_name, data):
        with self.lock:  # thread-safe lock 메커니즘 적용
            print(f"{tool_name}이(가) 데이터 처리를 시작합니다.")
            self.shared_memory[tool_name] = data
            time.sleep(2)  # 실제 도구 작업을 모의하기 위한 지연
            result = f"{tool_name} 처리 결과: {data[::-1]}"  # 간단한 처리 예시 (문자열 역순)
            print(f"{tool_name}이(가) 데이터 처리를 완료했습니다.")
            return result

if __name__ == "__main__":
    manager = ToolManager()

    # 병렬 도구 실행 테스트 함수 (실제 처리 로직 적용)
    def tool_task(tool_name, data):
        result = manager.execute_tool(tool_name, data)
        print(result)

    # 병렬 실행을 위한 실제 도구 스레드 생성
    thread1 = threading.Thread(target=tool_task, args=("Tool_A", "실제데이터1"))
    thread2 = threading.Thread(target=tool_task, args=("Tool_B", "실제데이터2"))

    # 스레드 시작
    thread1.start()
    thread2.start()

    # 모든 스레드 완료 대기
    thread1.join()
    thread2.join()

    print("모든 도구의 실제 병렬 처리 완료")


