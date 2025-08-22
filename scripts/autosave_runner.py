#!/usr/bin/env python3
# [ACTIVE] VELOS 운영 철학 선언문
# =========================================================
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

"""
VELOS Autosave Runner (Linux 포팅 버전)
- 파일 변경 감지 및 자동 실행
- PowerShell 버전을 Python으로 포팅
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 환경 설정
os.environ.setdefault("VELOS_ROOT", "/workspace")
os.environ.setdefault("PYTHONPATH", "/workspace")

# 경로 가져오기
sys.path.insert(0, "/workspace")
from modules.report_paths import ROOT, P

DEBOUNCE_MS = 1500
LOCK_FILE = P["LOGS"] / "run.lock"
LOG_FILE = P["LOGS"] / f"autosave_runner_{datetime.now().strftime('%Y%m%d')}.log"
last_run = 0

def log_message(msg):
    """로그 메시지 기록"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {msg}\n"
    print(log_entry.strip())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def kick_run(reason, path):
    """VELOS 실행 트리거"""
    global last_run
    now = int(time.time() * 1000)
    
    if now - last_run < DEBOUNCE_MS:
        return
        
    if LOCK_FILE.exists():
        log_message(f"skip(lock): {reason} :: {path}")
        return
        
    try:
        # 락 파일 생성
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.write_text("locked")
        
        log_message(f"preflight... ({reason} :: {path})")
        
        # preflight 검사 (간단한 버전)
        preflight_result = subprocess.run([
            "python3", "scripts/velos_master_scheduler.py", "--dry-run"
        ], capture_output=True, text=True, cwd="/workspace")
        
        if preflight_result.returncode != 0:
            log_message(f"preflight FAIL ({reason})")
            return
            
        log_message("run start")
        
        # VELOS 마스터 실행
        run_result = subprocess.run([
            "python3", "scripts/velos_master_scheduler.py"
        ], capture_output=True, text=True, cwd="/workspace")
        
        log_message("run done")
        
    except Exception as e:
        log_message(f"ERROR: {str(e)}")
    finally:
        # 락 파일 제거
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        last_run = int(time.time() * 1000)

class VelosFileHandler(FileSystemEventHandler):
    """VELOS 파일 변경 핸들러"""
    
    def __init__(self):
        self.extensions = {'.py', '.ps1', '.json'}
    
    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.suffix in self.extensions:
            log_message(f"event: Changed :: {file_path}")
            kick_run("Changed", str(file_path))
    
    def on_created(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.suffix in self.extensions:
            log_message(f"event: Created :: {file_path}")
            kick_run("Created", str(file_path))
    
    def on_moved(self, event):
        if event.is_directory:
            return
        file_path = Path(event.dest_path)
        if file_path.suffix in self.extensions:
            log_message(f"event: Renamed :: {file_path}")
            kick_run("Renamed", str(file_path))

def main():
    """메인 실행 함수"""
    log_message(f"watch start - ROOT: {ROOT}")
    
    # 파일 감시자 설정
    event_handler = VelosFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(ROOT), recursive=True)
    
    try:
        observer.start()
        log_message("✅ VELOS autosave_runner 시작됨")
        
        while True:
            time.sleep(0.4)
    except KeyboardInterrupt:
        log_message("종료 요청 받음")
    finally:
        observer.stop()
        observer.join()
        log_message("autosave_runner 종료됨")

if __name__ == "__main__":
    main()