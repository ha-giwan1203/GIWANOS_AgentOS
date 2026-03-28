# [ACTIVE] VELOS 성능 테스트 패키지
# [ACTIVE] VELOS 성능 테스트 및 벤치마크 모듈
# 
# 이 패키지는 VELOS 데이터베이스의 성능을 측정하고
# 다양한 워크로드에서의 동작을 검증합니다.

from .benchmark_suite import run_suite, BenchResult

__all__ = ['run_suite', 'BenchResult']
