#!/usr/bin/env python3
# VELOS 프로세스 모니터링 및 자동 복구 시스템
# 컴퓨터 멈춤 현상 방지를 위한 리소스 모니터링

import psutil
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any

class VelosProcessMonitor:
    """VELOS 프로세스 모니터링 및 자동 복구"""
    
    def __init__(self):
        self.root_path = Path("/home/user/webapp")
        self.log_file = self.root_path / "data" / "logs" / "process_monitor.json"
        self.max_cpu_percent = 80.0  # CPU 사용률 임계값
        self.max_memory_mb = 1024    # 메모리 사용량 임계값 (MB)
        
    def get_velos_processes(self) -> List[Dict[str, Any]]:
        """VELOS 관련 프로세스 찾기"""
        velos_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline.lower() for keyword in ['velos', 'giwanos', 'autosave_runner']):
                    velos_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline,
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024 if proc.info['memory_info'] else 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return velos_processes
    
    def check_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 상태 확인"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
    
    def check_problematic_processes(self, processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문제가 있는 프로세스 식별"""
        problematic = []
        
        for proc in processes:
            issues = []
            
            # CPU 사용률 체크
            if proc['cpu_percent'] > self.max_cpu_percent:
                issues.append(f"high_cpu_{proc['cpu_percent']:.1f}%")
            
            # 메모리 사용량 체크
            if proc['memory_mb'] > self.max_memory_mb:
                issues.append(f"high_memory_{proc['memory_mb']:.1f}MB")
            
            # 무한루프 의심 프로세스 (autosave_runner)
            if 'autosave_runner' in proc['cmdline'] and proc['cpu_percent'] > 10:
                issues.append("suspected_infinite_loop")
            
            if issues:
                proc['issues'] = issues
                problematic.append(proc)
        
        return problematic
    
    def terminate_problematic_process(self, proc_info: Dict[str, Any]) -> bool:
        """문제가 있는 프로세스 종료"""
        try:
            proc = psutil.Process(proc_info['pid'])
            proc.terminate()
            
            # 5초 대기 후 강제 종료
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()
            
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def log_monitoring_result(self, result: Dict[str, Any]):
        """모니터링 결과 로깅"""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 기존 로그 읽기
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 새 로그 추가
            logs.append({
                'timestamp': int(time.time()),
                'iso_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                **result
            })
            
            # 최근 100개만 유지
            logs = logs[-100:]
            
            # 저장
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"로깅 실패: {e}")
    
    def monitor_once(self) -> Dict[str, Any]:
        """한 번의 모니터링 실행"""
        
        # VELOS 프로세스 찾기
        velos_processes = self.get_velos_processes()
        
        # 시스템 리소스 확인
        system_resources = self.check_system_resources()
        
        # 문제가 있는 프로세스 식별
        problematic = self.check_problematic_processes(velos_processes)
        
        # 자동 복구 실행
        terminated = []
        for proc in problematic:
            if 'suspected_infinite_loop' in proc.get('issues', []):
                print(f"⚠️  무한루프 의심 프로세스 종료 시도: PID {proc['pid']}")
                if self.terminate_problematic_process(proc):
                    terminated.append(proc['pid'])
        
        result = {
            'total_velos_processes': len(velos_processes),
            'problematic_processes': len(problematic),
            'terminated_processes': terminated,
            'system_resources': system_resources,
            'velos_processes': velos_processes,
            'problematic_details': problematic
        }
        
        return result
    
    def run_continuous_monitoring(self, interval_seconds: int = 30):
        """지속적 모니터링 실행"""
        print(f"🔍 VELOS 프로세스 모니터링 시작 (간격: {interval_seconds}초)")
        
        while True:
            try:
                result = self.monitor_once()
                
                # 결과 출력
                if result['problematic_processes'] > 0:
                    print(f"⚠️  문제 프로세스 {result['problematic_processes']}개 발견")
                    for proc in result['problematic_details']:
                        print(f"   PID {proc['pid']}: {', '.join(proc['issues'])}")
                
                if result['terminated_processes']:
                    print(f"🛑 프로세스 종료됨: {result['terminated_processes']}")
                
                self.log_monitoring_result(result)
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n모니터링 중단됨")
                break
            except Exception as e:
                print(f"모니터링 오류: {e}")
                time.sleep(interval_seconds)

def main():
    monitor = VelosProcessMonitor()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        monitor.run_continuous_monitoring()
    else:
        # 한 번만 실행
        result = monitor.monitor_once()
        
        print("=== VELOS 프로세스 모니터링 결과 ===")
        print(f"VELOS 프로세스: {result['total_velos_processes']}개")
        print(f"문제 프로세스: {result['problematic_processes']}개")
        print(f"시스템 CPU: {result['system_resources']['cpu_percent']:.1f}%")
        print(f"시스템 메모리: {result['system_resources']['memory_percent']:.1f}%")
        
        if result['problematic_details']:
            print("\n문제 프로세스 상세:")
            for proc in result['problematic_details']:
                print(f"  PID {proc['pid']}: {proc['name']} - {', '.join(proc['issues'])}")
        
        monitor.log_monitoring_result(result)

if __name__ == "__main__":
    main()