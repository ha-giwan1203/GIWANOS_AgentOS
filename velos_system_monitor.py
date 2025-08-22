#!/usr/bin/env python3
# VELOS 시스템 모니터링 및 자동 복구 스크립트
# 컴퓨터 멈춤 현상 방지를 위한 예방적 모니터링

import os
import time
import json
import psutil
import threading
from pathlib import Path
from datetime import datetime, timedelta

class VelosSystemMonitor:
    def __init__(self):
        self.root_path = Path("C:\giwanos")
        self.monitoring = False
        self.max_memory_mb = 512  # 512MB 메모리 제한
        self.max_cpu_percent = 50  # 50% CPU 사용률 제한
        self.check_interval = 30  # 30초마다 체크
        
    def log(self, message, level="INFO"):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
        # 로그 파일에도 기록
        log_file = self.root_path / "data" / "logs" / "system_monitor.log"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{level}] {message}\n")
        except Exception:
            pass
    
    def check_memory_usage(self):
        """메모리 사용량 체크"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                if 'python' in proc.info['name'].lower() or 'powershell' in proc.info['name'].lower():
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    if memory_mb > self.max_memory_mb:
                        self.log(f"⚠️  높은 메모리 사용량 감지: {proc.info['name']} (PID: {proc.info['pid']}) - {memory_mb:.1f}MB", "WARN")
                        return False
            return True
        except Exception as e:
            self.log(f"메모리 체크 실패: {e}", "ERROR")
            return True
    
    def check_cpu_usage(self):
        """CPU 사용량 체크"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.max_cpu_percent:
                self.log(f"⚠️  높은 CPU 사용량 감지: {cpu_percent:.1f}%", "WARN")
                return False
            return True
        except Exception as e:
            self.log(f"CPU 체크 실패: {e}", "ERROR")
            return True
    
    def check_lock_files(self):
        """락 파일 상태 체크 및 자동 정리"""
        lock_files = [
            self.root_path / "data" / ".velos.py.lock",
            self.root_path / "data" / "memory" / "memory.flush.lock"
        ]
        
        cleaned = False
        for lock_file in lock_files:
            if lock_file.exists():
                try:
                    # 5분 이상 된 락 파일 자동 정리
                    stat = lock_file.stat()
                    if time.time() - stat.st_mtime > 300:
                        lock_file.unlink()
                        self.log(f"🧹 오래된 락 파일 자동 정리: {lock_file.name}")
                        cleaned = True
                except Exception as e:
                    self.log(f"락 파일 정리 실패 {lock_file.name}: {e}", "ERROR")
        
        return cleaned
    
    def check_disk_space(self):
        """디스크 공간 체크"""
        try:
            disk_usage = psutil.disk_usage(str(self.root_path))
            free_gb = disk_usage.free / 1024 / 1024 / 1024
            if free_gb < 1.0:  # 1GB 미만
                self.log(f"⚠️  디스크 공간 부족: {free_gb:.2f}GB 남음", "WARN")
                return False
            return True
        except Exception as e:
            self.log(f"디스크 체크 실패: {e}", "ERROR")
            return True
    
    def auto_recovery_actions(self):
        """자동 복구 작업"""
        self.log("🔧 자동 복구 작업 시작")
        
        # 1. 락 파일 정리
        self.check_lock_files()
        
        # 2. 메모리 정리 (가비지 컬렉션)
        import gc
        gc.collect()
        
        # 3. 시스템 헬스 로그 업데이트
        try:
            health_file = self.root_path / "data" / "logs" / "system_health.json"
            if health_file.exists():
                with open(health_file, 'r', encoding='utf-8') as f:
                    health = json.load(f)
            else:
                health = {}
            
            health.update({
                "auto_recovery_ts": int(time.time()),
                "auto_recovery_by": "velos_system_monitor",
                "last_monitor_check": int(time.time())
            })
            
            with open(health_file, 'w', encoding='utf-8') as f:
                json.dump(health, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.log(f"헬스 로그 업데이트 실패: {e}", "ERROR")
        
        self.log("✅ 자동 복구 작업 완료")
    
    def monitor_loop(self):
        """모니터링 루프"""
        self.log("🔍 VELOS 시스템 모니터링 시작")
        
        while self.monitoring:
            try:
                # 각종 체크 수행
                memory_ok = self.check_memory_usage()
                cpu_ok = self.check_cpu_usage()
                disk_ok = self.check_disk_space()
                self.check_lock_files()
                
                # 문제 발견 시 자동 복구
                if not (memory_ok and cpu_ok and disk_ok):
                    self.auto_recovery_actions()
                
                # 다음 체크까지 대기
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.log("사용자 중단 요청")
                break
            except Exception as e:
                self.log(f"모니터링 오류: {e}", "ERROR")
                time.sleep(5)  # 오류 시 짧은 대기
        
        self.log("🔍 VELOS 시스템 모니터링 종료")
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring:
            self.log("이미 모니터링 중입니다")
            return
        
        self.monitoring = True
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
        self.log("모니터링 중지 요청됨")

def main():
    print("=== VELOS 시스템 모니터 ===")
    print("컴퓨터 멈춤 현상 방지를 위한 예방적 모니터링 시작")
    print("Ctrl+C로 중지 가능")
    
    monitor = VelosSystemMonitor()
    
    try:
        # 초기 헬스체크
        monitor.log("초기 시스템 체크 수행")
        monitor.check_memory_usage()
        monitor.check_cpu_usage()
        monitor.check_disk_space()
        monitor.check_lock_files()
        
        # 모니터링 시작
        monitor_thread = monitor.start_monitoring()
        
        # 메인 스레드는 사용자 입력 대기
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n사용자 중단 요청됨")
        monitor.stop_monitoring()
        print("모니터링 종료")

if __name__ == "__main__":
    main()