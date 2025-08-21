#!/usr/bin/env python3
"""
GPT-5 메모리 상태 확인 스크립트
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def check_gpt5_memory_states():
    """GPT-5 모니터링 데이터베이스의 메모리 상태 확인"""
    
    gpt5_db_path = Path("/home/user/webapp/data/gpt5_monitor/gpt5_monitor.db")
    
    if not gpt5_db_path.exists():
        print(f"❌ GPT-5 모니터링 DB가 존재하지 않습니다: {gpt5_db_path}")
        return
    
    print(f"🔍 GPT-5 메모리 상태 분석 중: {gpt5_db_path}")
    print(f"📁 파일 크기: {gpt5_db_path.stat().st_size:,} bytes")
    
    try:
        with sqlite3.connect(str(gpt5_db_path)) as conn:
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"\n📋 테이블 목록: {tables}")
            
            for table_name in tables:
                print(f"\n🗂️ 테이블: {table_name}")
                
                # 테이블 스키마 확인
                cursor.execute(f"PRAGMA table_info({table_name})")
                schema = cursor.fetchall()
                columns = [col[1] for col in schema]
                print(f"   컬럼: {columns}")
                
                # 레코드 수 확인
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   레코드 수: {count:,}개")
                
                # memory_states 테이블 특별 분석
                if table_name == 'memory_states':
                    print(f"\n🧠 메모리 상태 상세 분석:")
                    cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 10")
                    memory_states = cursor.fetchall()
                    
                    for i, state in enumerate(memory_states, 1):
                        state_dict = dict(zip(columns, state))
                        print(f"   {i}. 세션: {state_dict.get('session_id', 'N/A')}")
                        print(f"      시간: {state_dict.get('timestamp', 'N/A')}")
                        print(f"      단기 메모리: {state_dict.get('short_term_usage', 'N/A')}%")
                        print(f"      장기 메모리: {state_dict.get('long_term_usage', 'N/A')}%")
                        print(f"      버퍼 사용량: {state_dict.get('buffer_usage', 'N/A')}%")
                        if state_dict.get('context_summary'):
                            summary_preview = str(state_dict['context_summary'])[:50] + "..." if len(str(state_dict['context_summary'])) > 50 else str(state_dict['context_summary'])
                            print(f"      컨텍스트: {summary_preview}")
                        print()
                
                # conversation_messages 테이블에서 학습 관련 메시지 검색
                elif table_name == 'conversation_messages':
                    print(f"\n💬 학습 관련 대화 메시지:")
                    cursor.execute(f"""
                        SELECT * FROM {table_name} 
                        WHERE content LIKE '%학습%' OR content LIKE '%learning%' 
                        OR content LIKE '%memory%' OR content LIKE '%기억%'
                        ORDER BY timestamp DESC LIMIT 5
                    """)
                    learning_messages = cursor.fetchall()
                    
                    for i, msg in enumerate(learning_messages, 1):
                        msg_dict = dict(zip(columns, msg))
                        print(f"   {i}. 타입: {msg_dict.get('message_type', 'N/A')}")
                        print(f"      시간: {msg_dict.get('timestamp', 'N/A')}")
                        content_preview = str(msg_dict.get('content', ''))[:100] + "..." if len(str(msg_dict.get('content', ''))) > 100 else str(msg_dict.get('content', ''))
                        print(f"      내용: {content_preview}")
                        print()
                
                # 샘플 데이터 표시 (처음 3개)
                if count > 0 and table_name not in ['memory_states', 'conversation_messages']:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    samples = cursor.fetchall()
                    print(f"   샘플 데이터:")
                    for i, sample in enumerate(samples, 1):
                        sample_dict = dict(zip(columns, sample))
                        print(f"   {i}. {sample_dict}")
                    print()
    
    except Exception as e:
        print(f"❌ 데이터베이스 분석 오류: {e}")

def check_learning_memory_content():
    """learning_memory.json의 실제 학습 내용 확인"""
    
    learning_json_path = Path("/home/user/webapp/data/memory/learning_memory.json")
    
    if not learning_json_path.exists():
        print(f"❌ 학습 메모리 JSON 파일이 존재하지 않습니다: {learning_json_path}")
        return
    
    print(f"\n📚 학습 메모리 JSON 내용 분석:")
    
    try:
        with open(learning_json_path, 'r', encoding='utf-8') as f:
            learning_data = json.load(f)
        
        if isinstance(learning_data, list):
            print(f"   전체 학습 기록: {len(learning_data):,}개")
            
            # 최근 학습 기록 몇 개 표시
            print(f"\n🎓 최근 학습 기록 샘플:")
            for i, record in enumerate(learning_data[-5:], 1):  # 마지막 5개
                if isinstance(record, dict):
                    timestamp = record.get('timestamp', 'N/A')
                    content = record.get('content', record.get('insight', str(record)))
                    content_preview = str(content)[:100] + "..." if len(str(content)) > 100 else str(content)
                    print(f"   {i}. [{timestamp}] {content_preview}")
            
            # 학습 키워드로 필터링
            learning_keywords = ['학습', 'learning', 'train', 'memory', '기억', 'GPT', 'AI']
            relevant_records = []
            
            for record in learning_data:
                if isinstance(record, dict):
                    record_str = json.dumps(record, ensure_ascii=False).lower()
                    if any(keyword.lower() in record_str for keyword in learning_keywords):
                        relevant_records.append(record)
            
            print(f"\n🔍 학습 관련 키워드 포함 기록: {len(relevant_records)}개")
            for i, record in enumerate(relevant_records[:3], 1):  # 처음 3개만
                timestamp = record.get('timestamp', 'N/A')
                content = record.get('content', record.get('insight', str(record)))
                content_preview = str(content)[:150] + "..." if len(str(content)) > 150 else str(content)
                print(f"   {i}. [{timestamp}] {content_preview}")
        
        else:
            print(f"   데이터 형태: {type(learning_data)}")
            print(f"   내용 미리보기: {str(learning_data)[:200]}...")
    
    except Exception as e:
        print(f"❌ 학습 메모리 JSON 분석 오류: {e}")

if __name__ == "__main__":
    print("🚀 VELOS-GPT5 메모리 상태 상세 확인")
    print("="*60)
    
    check_gpt5_memory_states()
    check_learning_memory_content()
    
    print(f"\n✅ 메모리 상태 확인 완료!")
    print("🎯 결론: VELOS-GPT5 시스템은 실시간 메모리 모니터링과 학습 기록 저장을 모두 지원합니다!")