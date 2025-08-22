#!/usr/bin/env python3
# [ACTIVE] VELOS-GPT5 모니터링 시스템 테스트 스크립트
# 실행: python scripts/test_gpt5_monitor.py

import sys
import time
import random
from pathlib import Path
from datetime import datetime

# VELOS 루트 경로를 Python 경로에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from modules.gpt5_monitor import get_gpt5_monitor
from modules.gpt5_reports import get_report_generator


def test_basic_monitoring():
    """기본 모니터링 기능 테스트"""
    print("🧪 기본 모니터링 기능 테스트 시작...")
    
    monitor = get_gpt5_monitor()
    
    # 1. 테스트 세션 시작
    test_session_id = f"test_session_{int(datetime.now().timestamp())}"
    print(f"세션 시작: {test_session_id}")
    
    success = monitor.start_session(test_session_id)
    if success:
        print("✅ 세션 시작 성공")
    else:
        print("❌ 세션 시작 실패")
        return False
    
    # 2. 모니터링 데이터 기록
    print("모니터링 데이터 기록 중...")
    
    for i in range(5):
        # 메모리 상태 기록
        memory_data = {
            'short_term': random.uniform(20, 80),
            'long_term': random.uniform(40, 90),  
            'buffer': random.uniform(10, 50),
            'total_mb': random.uniform(100, 500)
        }
        monitor.record_memory_state(test_session_id, memory_data)
        
        # 맥락 상태 기록
        context_data = {
            'windows': random.randint(8, 15),
            'coherence_score': random.uniform(0.7, 0.98),
            'context_length': random.randint(1000, 5000),
            'degradation_risk': random.uniform(0.1, 0.5)
        }
        monitor.record_context_state(test_session_id, context_data)
        
        # 성능 메트릭 기록
        perf_data = {
            'response_time_ms': random.randint(500, 3000),
            'tokens_processed': random.randint(100, 1000),
            'api_calls': random.randint(1, 10),
            'errors': random.randint(0, 2)
        }
        monitor.record_performance(test_session_id, perf_data)
        
        print(f"  데이터 세트 {i+1}/5 기록 완료")
        time.sleep(0.5)
    
    print("✅ 모니터링 데이터 기록 완료")
    
    # 3. 데이터 조회 테스트
    print("데이터 조회 테스트...")
    
    active_sessions = monitor.get_active_sessions()
    print(f"활성 세션 수: {len(active_sessions)}")
    
    analytics = monitor.get_session_analytics(test_session_id, 1)
    if analytics:
        print("✅ 세션 분석 데이터 조회 성공")
    else:
        print("❌ 세션 분석 데이터 조회 실패")
    
    health = monitor.get_system_health()
    if health:
        print("✅ 시스템 헬스 조회 성공")
        print(f"  CPU: {health['system']['cpu_percent']:.1f}%")
        print(f"  메모리: {health['system']['memory_percent']:.1f}%")
        print(f"  활성 세션: {health['gpt5']['active_sessions']}")
    else:
        print("❌ 시스템 헬스 조회 실패")
    
    # 4. 세션 종료
    print(f"세션 종료: {test_session_id}")
    success = monitor.end_session(test_session_id)
    if success:
        print("✅ 세션 종료 성공")
    else:
        print("❌ 세션 종료 실패")
    
    return True


def test_report_generation():
    """보고서 생성 기능 테스트"""
    print("\n📋 보고서 생성 기능 테스트 시작...")
    
    report_gen = get_report_generator()
    
    # 1. 실시간 상태 보고서 생성
    print("실시간 상태 보고서 생성 중...")
    realtime_report = report_gen.generate_realtime_report()
    
    if realtime_report:
        print("✅ 실시간 보고서 생성 성공")
        print(f"  보고서 ID: {realtime_report['id']}")
        print(f"  파일 경로: {realtime_report['file_path']}")
    else:
        print("❌ 실시간 보고서 생성 실패")
        return False
    
    # 2. 성능 분석 보고서 생성
    print("성능 분석 보고서 생성 중...")
    performance_report = report_gen.generate_performance_report(24)
    
    if performance_report:
        print("✅ 성능 보고서 생성 성공")
        print(f"  보고서 ID: {performance_report['id']}")
        print(f"  파일 경로: {performance_report['file_path']}")
    else:
        print("❌ 성능 보고서 생성 실패")
        return False
    
    # 3. 보고서 전송 로그 테스트
    monitor = get_gpt5_monitor()
    
    transmission_data = {
        'report_id': realtime_report['id'],
        'report_type': 'realtime_status',
        'recipient': 'test@velos.ai',
        'method': 'email',
        'status': 'success',
        'file_path': realtime_report['file_path'],
        'metadata': {'test': True}
    }
    
    success = monitor.log_report_transmission(transmission_data)
    if success:
        print("✅ 보고서 전송 로그 기록 성공")
    else:
        print("❌ 보고서 전송 로그 기록 실패")
    
    return True


def create_demo_data():
    """데모용 데이터 생성"""
    print("\n🎭 데모 데이터 생성 시작...")
    
    monitor = get_gpt5_monitor()
    
    # 여러 개의 테스트 세션 생성
    demo_sessions = []
    for i in range(3):
        session_id = f"demo_session_{i+1}_{int(datetime.now().timestamp())}"
        demo_sessions.append(session_id)
        
        monitor.start_session(session_id)
        print(f"데모 세션 생성: {session_id}")
        
        # 각 세션에 랜덤 데이터 추가
        for j in range(10):
            # 메모리 데이터 (시간에 따라 변화하는 패턴)
            base_memory = 200 + i * 100
            memory_data = {
                'short_term': base_memory * random.uniform(0.3, 0.8),
                'long_term': base_memory * random.uniform(0.4, 0.9),
                'buffer': base_memory * random.uniform(0.1, 0.4),
                'total_mb': base_memory * random.uniform(0.8, 1.2)
            }
            monitor.record_memory_state(session_id, memory_data)
            
            # 맥락 데이터 (품질이 시간에 따라 약간 저하)
            quality_degradation = j * 0.01
            context_data = {
                'windows': random.randint(10, 15) - j // 3,
                'coherence_score': random.uniform(0.85, 0.98) - quality_degradation,
                'context_length': random.randint(2000, 6000) + j * 200,
                'degradation_risk': random.uniform(0.1, 0.3) + quality_degradation
            }
            monitor.record_context_state(session_id, context_data)
            
            # 성능 데이터 (부하에 따라 응답시간 증가)
            load_factor = 1 + (j * 0.1)
            perf_data = {
                'response_time_ms': int(random.randint(800, 1500) * load_factor),
                'tokens_processed': random.randint(150, 800),
                'api_calls': random.randint(2, 8),
                'errors': random.randint(0, 1) if j > 7 else 0
            }
            monitor.record_performance(session_id, perf_data)
            
            time.sleep(0.1)  # 약간의 지연
    
    print(f"✅ {len(demo_sessions)}개의 데모 세션 생성 완료")
    
    # 데모 보고서 생성
    print("데모 보고서 생성 중...")
    report_gen = get_report_generator()
    
    # 실시간 보고서
    realtime_report = report_gen.generate_realtime_report()
    if realtime_report:
        print(f"✅ 데모 실시간 보고서: {realtime_report['file_path']}")
    
    # 성능 보고서
    performance_report = report_gen.generate_performance_report(1)
    if performance_report:
        print(f"✅ 데모 성능 보고서: {performance_report['file_path']}")
    
    return demo_sessions


def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("🧠 VELOS-GPT5 모니터링 시스템 테스트")
    print("=" * 60)
    
    try:
        # 1. 기본 기능 테스트
        if not test_basic_monitoring():
            print("❌ 기본 모니터링 테스트 실패")
            return
        
        # 2. 보고서 생성 테스트
        if not test_report_generation():
            print("❌ 보고서 생성 테스트 실패")
            return
        
        # 3. 데모 데이터 생성
        demo_sessions = create_demo_data()
        
        print("\n" + "=" * 60)
        print("🎉 모든 테스트 완료!")
        print("=" * 60)
        print("\n📊 대시보드 실행 방법:")
        print("  streamlit run scripts/gpt5_dashboard_app.py")
        print("\n📋 생성된 데모 세션:")
        for session in demo_sessions:
            print(f"  - {session}")
        
        # 시스템 상태 요약
        monitor = get_gpt5_monitor()
        health = monitor.get_system_health()
        if health:
            print(f"\n🏥 현재 시스템 상태:")
            print(f"  활성 세션: {health['gpt5']['active_sessions']}개")
            print(f"  CPU: {health['system']['cpu_percent']:.1f}%")
            print(f"  메모리: {health['system']['memory_percent']:.1f}%")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()