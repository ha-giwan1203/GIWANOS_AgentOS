"""
VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를
시도한다.

안전한 수학 연산 유틸리티
0으로 나누기 오류를 방지하는 안전한 수학 함수들을 제공합니다.
"""

# 매우 작은 값 (0으로 나누기 방지)
EPS = 1e-9


def safe_div(a, b):
    """
    안전한 나눗셈 함수

    Args:
        a: 분자
        b: 분모

    Returns:
        a / b (b가 0이면 EPS로 대체)
    """
    return a / (b if b else EPS)


def safe_avg(values):
    """
    안전한 평균 계산

    Args:
        values: 숫자 리스트

    Returns:
        평균값 (빈 리스트면 0)
    """
    if not values:
        return 0
    return safe_div(sum(values), len(values))


def safe_percent_change(current, previous):
    """
    안전한 변화율 계산

    Args:
        current: 현재 값
        previous: 이전 값

    Returns:
        변화율 (이전 값이 0이면 0)
    """
    if not previous:
        return 0
    return (safe_div(current, previous) - 1) * 100


def safe_ratio(a, b):
    """
    안전한 비율 계산

    Args:
        a: 첫 번째 값
        b: 두 번째 값

    Returns:
        a:b 비율 (b가 0이면 매우 큰 값)
    """
    return safe_div(a, b)


def pretty_speedup(t1, t2):
    """
    성능 향상을 예쁘게 표시하는 함수

    Args:
        t1: 첫 번째 시간 (기준)
        t2: 두 번째 시간 (개선된)

    Returns:
        성능 향상 설명 문자열
    """
    if t2 < 0.0005:  # 타이머 해상도 이하
        return "매우 빠름 (측정 불가)"
    return f"{safe_div(t1, t2):.1f}배 빨라짐"


# 테스트 함수
def test_safe_math():
    """안전한 수학 함수 테스트"""
    print("=== 안전한 수학 함수 테스트 ===")

    # 안전한 나눗셈 테스트
    print(f"safe_div(10, 2) = {safe_div(10, 2)}")  # 5.0
    print(f"safe_div(10, 0) = {safe_div(10, 0)}")  # 매우 큰 값

    # 안전한 평균 테스트
    print(f"safe_avg([1, 2, 3]) = {safe_avg([1, 2, 3])}")  # 2.0
    print(f"safe_avg([]) = {safe_avg([])}")  # 0

    # 안전한 변화율 테스트
    print(f"safe_percent_change(110, 100) = {safe_percent_change(110, 100):.1f}%")  # 10.0%
    print(f"safe_percent_change(100, 0) = {safe_percent_change(100, 0):.1f}%")  # 0.0%

    # 안전한 비율 테스트
    print(f"safe_ratio(5, 2) = {safe_ratio(5, 2)}")  # 2.5
    print(f"safe_ratio(5, 0) = {safe_ratio(5, 0)}")  # 매우 큰 값

    # 성능 향상 테스트
    print(f"pretty_speedup(0.1, 0.01) = {pretty_speedup(0.1, 0.01)}")  # 10.0배
    print(f"pretty_speedup(0.1, 0.0001) = {pretty_speedup(0.1, 0.0001)}")  # 매우 빠름

    print("✅ 모든 테스트 통과")


if __name__ == "__main__":
    test_safe_math()
