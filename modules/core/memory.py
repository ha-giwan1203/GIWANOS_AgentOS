"""
File: C:/giwanos/core/memory.py

설명:
- 판단 컨텍스트로 사용할 최신 시스템 메트릭 및 예시 context 제공
- JudgeAgent._gather_context에서 호출됩니다
"""

import psutil

def get_latest_metrics() -> dict:
    """
    시스템 상태를 기반으로 판단에 필요한 context를 반환합니다.
    필요에 따라 필드를 추가·변경하세요.
    """
    return {
        # 예시: 연령(age) 필드를 20으로 제공하여 rule_001을 매칭 가능하게 함
        "age": 20,
        # 실행 환경 메트릭 예시
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }
