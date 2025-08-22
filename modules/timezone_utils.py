# [ACTIVE] VELOS 시간대 유틸리티 - 한국시간 안정성 보장
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

# 한국 시간대 상수
KOREA_TZ = timezone(timedelta(hours=9))

def ensure_korean_timezone():
    """한국시간대 설정 보장"""
    os.environ['TZ'] = 'Asia/Seoul'
    time.tzset()

def get_korean_now() -> datetime:
    """현재 한국시간 반환 (timezone-aware)"""
    ensure_korean_timezone()
    return datetime.now(KOREA_TZ)

def get_korean_timestamp() -> str:
    """한국시간 타임스탬프 문자열 반환"""
    return get_korean_now().strftime('%Y-%m-%d %H:%M:%S')

def get_korean_timestamp_detailed() -> str:
    """상세한 한국시간 타임스탬프 (KST 표시 포함)"""
    return get_korean_now().strftime('%Y-%m-%d %H:%M:%S KST')

def convert_to_korean_time(dt: datetime) -> datetime:
    """datetime 객체를 한국시간으로 변환"""
    if dt.tzinfo is None:
        # timezone 정보가 없으면 UTC로 가정
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KOREA_TZ)

def is_korean_timezone_set() -> bool:
    """한국시간대가 올바르게 설정되었는지 확인"""
    ensure_korean_timezone()
    local_now = datetime.now()
    utc_now = datetime.now(timezone.utc)
    korea_now = datetime.now(KOREA_TZ)
    
    # 로컬 시간과 한국시간이 같은지 확인 (분 단위까지)
    return (abs((local_now - korea_now.replace(tzinfo=None)).total_seconds()) < 60)

def validate_timezone_consistency() -> dict:
    """시간대 일관성 검증"""
    ensure_korean_timezone()
    
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()
    korea_now = datetime.now(KOREA_TZ)
    
    time_diff = korea_now.hour - utc_now.hour
    if time_diff < 0:
        time_diff += 24
    
    return {
        'utc_time': utc_now.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'local_time': local_now.strftime('%Y-%m-%d %H:%M:%S'),
        'korea_time': korea_now.strftime('%Y-%m-%d %H:%M:%S KST'),
        'time_diff_hours': time_diff,
        'is_correct': time_diff == 9,
        'is_consistent': is_korean_timezone_set(),
        'tz_env': os.environ.get('TZ', 'Not set')
    }

# 모듈 import 시 자동으로 한국시간 설정
ensure_korean_timezone()

if __name__ == "__main__":
    # 테스트 실행
    print("=== 한국시간 유틸리티 테스트 ===")
    validation = validate_timezone_consistency()
    
    for key, value in validation.items():
        print(f"{key}: {value}")
    
    if validation['is_correct'] and validation['is_consistent']:
        print("\n✅ 한국시간 설정 완벽!")
    else:
        print("\n⚠️  한국시간 설정 확인 필요")