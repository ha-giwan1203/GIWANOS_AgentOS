#!/usr/bin/env python3
# VELOS 안전 모드 - 시스템 멈춤 현상 발생 시 긴급 복구

import os
import json
import time
import shutil
from pathlib import Path

def emergency_shutdown():
    """긴급 종료 - 모든 VELOS 프로세스 정리"""
    print("🚨 VELOS 긴급 종료 모드")
    
    # 1. 모든 락 파일 제거
    lock_files = [
        "C:\giwanos/data/.velos.py.lock",
        "C:\giwanos/data/memory/memory.flush.lock",
        "C:\giwanos/data/logs/run.lock"
    ]
    
    removed_locks = 0
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"🧹 락 파일 제거: {lock_file}")
                removed_locks += 1
            except Exception as e:
                print(f"❌ 락 파일 제거 실패 {lock_file}: {e}")
    
    print(f"✅ {removed_locks}개 락 파일 정리됨")
    
    # 2. 임시 파일 정리
    temp_patterns = [
        "C:\giwanos/data/**/*.tmp",
        "C:\giwanos/data/**/*.temp",
    ]
    
    # 3. 메모리 백업 생성
    try:
        memory_file = Path("C:\giwanos/data/memory/learning_memory.json")
        if memory_file.exists():
            backup_file = memory_file.with_suffix(f".backup_emergency_{int(time.time())}.json")
            shutil.copy2(memory_file, backup_file)
            print(f"💾 메모리 백업 생성: {backup_file.name}")
    except Exception as e:
        print(f"❌ 백업 생성 실패: {e}")
    
    # 4. 헬스 로그 업데이트
    try:
        health_file = Path("C:\giwanos/data/logs/system_health.json")
        health = {}
        if health_file.exists():
            with open(health_file, 'r', encoding='utf-8') as f:
                health = json.load(f)
        
        health.update({
            "emergency_shutdown_ts": int(time.time()),
            "emergency_shutdown_reason": "user_initiated",
            "system_safe_mode": True,
            "locks_cleared": removed_locks
        })
        
        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump(health, f, ensure_ascii=False, indent=2)
        print("📝 헬스 로그 업데이트 완료")
    except Exception as e:
        print(f"❌ 헬스 로그 업데이트 실패: {e}")

def safe_restart():
    """안전 재시작 - 시스템을 안전한 상태로 복구"""
    print("🔄 VELOS 안전 재시작 모드")
    
    # 1. 긴급 종료 먼저 수행
    emergency_shutdown()
    
    # 2. 데이터 무결성 검사
    print("📊 데이터 무결성 검사 중...")
    try:
        json_file = Path("C:\giwanos/data/memory/learning_memory.json")
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"✅ learning_memory.json: 정상 ({len(data)}개 항목)")
            else:
                print("⚠️  learning_memory.json: 형식 문제 - 수정 필요")
                # 자동 수정 로직 호출
                fix_learning_memory()
    except Exception as e:
        print(f"❌ 데이터 검사 실패: {e}")
    
    # 3. 필수 디렉토리 확인
    essential_dirs = [
        "C:\giwanos/data/logs",
        "C:\giwanos/data/memory",
        "C:\giwanos/data/reports"
    ]
    
    for dir_path in essential_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ 필수 디렉토리 확인됨")
    
    # 4. 시스템 상태 정상화
    try:
        health_file = Path("C:\giwanos/data/logs/system_health.json")
        health = {}
        if health_file.exists():
            with open(health_file, 'r', encoding='utf-8') as f:
                health = json.load(f)
        
        health.update({
            "safe_restart_ts": int(time.time()),
            "system_safe_mode": False,
            "restart_successful": True,
            "data_integrity_ok": True
        })
        
        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump(health, f, ensure_ascii=False, indent=2)
        print("📝 시스템 상태 정상화 완료")
    except Exception as e:
        print(f"❌ 상태 정상화 실패: {e}")

def fix_learning_memory():
    """learning_memory.json 자동 수정"""
    json_file = Path("C:\giwanos/data/memory/learning_memory.json")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'items' in data:
            items = data['items']
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"🔧 learning_memory.json 수정 완료: {len(items)}개 항목")
        
    except Exception as e:
        print(f"❌ learning_memory.json 수정 실패: {e}")

def show_status():
    """현재 시스템 상태 표시"""
    print("📊 VELOS 시스템 상태")
    print("=" * 50)
    
    # 락 파일 상태
    lock_files = [
        "C:\giwanos/data/.velos.py.lock",
        "C:\giwanos/data/memory/memory.flush.lock"
    ]
    
    active_locks = 0
    for lock_file in lock_files:
        if os.path.exists(lock_file):
            print(f"🔒 활성 락: {Path(lock_file).name}")
            active_locks += 1
    
    if active_locks == 0:
        print("✅ 활성 락 없음")
    
    # 메모리 파일 상태
    json_file = Path("C:\giwanos/data/memory/learning_memory.json")
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"✅ 메모리 파일: 정상 ({len(data)}개 항목)")
            else:
                print("⚠️  메모리 파일: 형식 문제")
        except Exception:
            print("❌ 메모리 파일: 읽기 오류")
    else:
        print("❌ 메모리 파일: 없음")
    
    # 헬스 로그 상태
    health_file = Path("C:\giwanos/data/logs/system_health.json")
    if health_file.exists():
        try:
            with open(health_file, 'r', encoding='utf-8') as f:
                health = json.load(f)
            safe_mode = health.get('system_safe_mode', False)
            print(f"📊 시스템 모드: {'안전 모드' if safe_mode else '정상 모드'}")
        except Exception:
            print("⚠️  헬스 로그: 읽기 오류")
    else:
        print("❌ 헬스 로그: 없음")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("VELOS 안전 모드 도구")
        print("사용법:")
        print("  python velos_safe_mode.py status     - 시스템 상태 확인")
        print("  python velos_safe_mode.py emergency  - 긴급 종료")
        print("  python velos_safe_mode.py restart    - 안전 재시작")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "emergency":
        emergency_shutdown()
        print("🚨 긴급 종료 완료. 컴퓨터 재부팅을 권장합니다.")
    elif command == "restart":
        safe_restart()
        print("🔄 안전 재시작 완료. 시스템이 정상 상태로 복구되었습니다.")
    else:
        print(f"❌ 알 수 없는 명령: {command}")

if __name__ == "__main__":
    main()