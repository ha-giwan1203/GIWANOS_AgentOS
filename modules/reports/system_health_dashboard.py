#!/usr/bin/env python3
# =========================================================
# VELOS 시스템 건강 대시보드 생성기
# 실제 유용한 정보와 인사이트 제공
# =========================================================

import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Use correct path for sandbox environment
ROOT = Path("C:\giwanos")

class SystemHealthAnalyzer:
    """시스템 건강 상태 분석기"""
    
    def __init__(self):
        # Force correct path for sandbox environment
        self.root = Path("C:\giwanos")
        self.logs_dir = self.root / "data" / "logs"
        self.memory_dir = self.root / "data" / "memory"
        self.reports_dir = self.root / "data" / "reports"
        
    def load_json_safe(self, file_path: Path) -> Dict[str, Any]:
        """안전한 JSON 로딩"""
        if not file_path.exists():
            return {}
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] JSON 로딩 실패 {file_path}: {e}")
            return {}
    
    def analyze_system_integrity(self) -> Dict[str, Any]:
        """시스템 무결성 분석"""
        health_data = self.load_json_safe(self.logs_dir / "system_health.json")
        
        analysis = {
            "status": "unknown",
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "metrics": {}
        }
        
        if not health_data:
            analysis["status"] = "error"
            analysis["critical_issues"].append("시스템 헬스 데이터 없음 - 모니터링 시스템 점검 필요")
            return analysis
        
        # 시스템 무결성 체크 - 실제 데이터 기반 분석
        sys_integrity = health_data.get("system_integrity", {})
        overall_status = health_data.get("overall_status", "UNKNOWN")
        
        # 프로세스 이슈 분석
        process_issues = sys_integrity.get("details", {}).get("process_issues", [])
        if process_issues:
            for issue in process_issues:
                if "autosave_runner" in issue:
                    analysis["critical_issues"].append("🚨 AutoSave Runner 중단됨 - 메모리 동기화 위험")
                    analysis["recommendations"].append("즉시 조치: autosave_runner 프로세스 재시작 필요")
                else:
                    analysis["warnings"].append(f"⚠️ 프로세스 이슈: {issue}")
        
        # 실제 데이터 무결성 분석
        data_integrity_ok = health_data.get("data_integrity_ok", False)
        if not data_integrity_ok:
            data_issues = health_data.get("data_integrity_issues", [])
            for issue in data_issues:
                if "learning_memory.json" in issue:
                    analysis["warnings"].append("⚠️ 학습 메모리 포맷 오류 감지")
                    analysis["recommendations"].append("📋 learning_memory.json 파일 구조 검증 필요")
        
        # 실제 메모리 상태 분석 - 1437개 레코드 기반
        memory_stats = health_data.get("memory_tick_stats", {})
        db_records = memory_stats.get("db_records", 0)
        buffer_size = memory_stats.get("buffer_size", 0)
        last_sync = memory_stats.get("last_sync", 0)
        
        analysis["metrics"]["db_records"] = db_records
        analysis["metrics"]["buffer_size"] = buffer_size 
        analysis["metrics"]["last_sync"] = last_sync
        analysis["metrics"]["overall_status"] = overall_status
        
        if db_records > 1000:
            analysis["metrics"]["memory_health"] = "우수"
            analysis["recommendations"].append(f"✅ 메모리 레코드 {db_records:,}개 - 풍부한 학습 데이터 보유")
        elif db_records > 100:
            analysis["metrics"]["memory_health"] = "양호"
        else:
            analysis["warnings"].append("⚠️ 메모리 DB 레코드 부족 - 학습 데이터 축적 필요")
        
        # 스냅샷 및 백업 상태
        snapshot_ok = health_data.get("snapshot_integrity_ok", False)
        snapshot_entries = health_data.get("snapshot_catalog_entries", 0)
        if snapshot_ok and snapshot_entries > 0:
            analysis["metrics"]["backup_status"] = f"정상 ({snapshot_entries}개 스냅샷)"
            if snapshot_entries >= 15:
                analysis["recommendations"].append("✅ 충분한 백업 스냅샷 유지 중")
        else:
            analysis["warnings"].append("⚠️ 백업 스냅샷 상태 점검 필요")
        
        # 전체 상태 판정 - 실제 데이터 기반
        if analysis["critical_issues"]:
            analysis["status"] = "critical"
        elif analysis["warnings"]:
            analysis["status"] = "warning" 
        elif overall_status == "OK" and db_records > 1000:
            analysis["status"] = "healthy"
        else:
            analysis["status"] = "monitoring"
        
        return analysis
    
    def analyze_performance(self) -> Dict[str, Any]:
        """실제 데이터 기반 성능 분석"""
        health_data = self.load_json_safe(self.logs_dir / "system_health.json")
        
        performance = {
            "memory_efficiency": "unknown", 
            "io_performance": "unknown",
            "sync_status": "unknown",
            "bottlenecks": [],
            "optimizations": [],
            "metrics": {}
        }
        
        # 메모리 동기화 성능 - 실제 타임스탬프 기반
        memory_tick_ts = health_data.get("memory_tick_last_ts", 0)
        memory_stats = health_data.get("memory_tick_stats", {})
        last_sync = memory_stats.get("last_sync", 0)
        
        if memory_tick_ts > 0 and last_sync > 0:
            sync_gap = abs(memory_tick_ts - last_sync)
            performance["metrics"]["sync_gap_seconds"] = sync_gap
            
            if sync_gap < 60:  # 1분 이내
                performance["memory_efficiency"] = "우수"
                performance["sync_status"] = "실시간"
            elif sync_gap < 300:  # 5분 이내
                performance["memory_efficiency"] = "양호"  
                performance["sync_status"] = "정상"
            else:
                performance["memory_efficiency"] = "지연"
                performance["sync_status"] = "지연"
                performance["bottlenecks"].append(f"메모리 동기화 {sync_gap//60}분 지연")
        
        # HotBuffer 성능 분석
        hotbuf_ok = health_data.get("hotbuf_ok", False)
        hotbuf_rebuild_count = health_data.get("hotbuf_rebuild_count", 0)
        
        if hotbuf_ok:
            performance["io_performance"] = "정상"
            performance["metrics"]["hotbuf_rebuilds"] = hotbuf_rebuild_count
            
            if hotbuf_rebuild_count > 30:
                performance["optimizations"].append("HotBuffer 재빌드 횟수 많음 - TTL 조정 고려")
            elif hotbuf_rebuild_count < 5:
                performance["optimizations"].append("✅ HotBuffer 안정적 운영 중")
        else:
            performance["io_performance"] = "오류"
            performance["bottlenecks"].append("HotBuffer 빌드 실패")
        
        # DB 레코드 기반 처리량 분석  
        db_records = memory_stats.get("db_records", 0)
        buffer_size = memory_stats.get("buffer_size", 0)
        
        performance["metrics"]["total_records"] = db_records
        performance["metrics"]["buffer_utilization"] = f"{buffer_size} records"
        
        if db_records > 1000:
            processing_efficiency = "고효율" if buffer_size < 100 else "보통"
            performance["optimizations"].append(f"✅ 대용량 데이터 {processing_efficiency} 처리 중")
        
        # 세션 부트스트랩 성능
        bootstrap_ok = health_data.get("session_bootstrap_ok", False)
        bootstrap_moved = health_data.get("session_bootstrap_flush_moved", 0)
        
        if bootstrap_ok and bootstrap_moved > 0:
            performance["metrics"]["bootstrap_efficiency"] = f"{bootstrap_moved} records processed"
            performance["optimizations"].append("✅ 세션 부트스트랩 정상 완료")
        
        return performance
    
    def get_recent_activities(self) -> List[Dict[str, Any]]:
        """최근 활동 분석"""
        activities = []
        
        # 메모리 파일 체크
        memory_file = self.memory_dir / "autosave_inbox.jsonl"
        if memory_file.exists():
            try:
                lines = memory_file.read_text(encoding="utf-8").strip().split('\n')
                recent_count = len([l for l in lines[-10:] if l.strip()])
                activities.append({
                    "type": "memory",
                    "description": f"최근 메모리 활동 {recent_count}건",
                    "status": "normal" if recent_count > 0 else "low"
                })
            except Exception:
                pass
        
        # 로그 활동 체크
        log_files = list(self.logs_dir.glob("*.log"))
        recent_logs = 0
        for log_file in log_files:
            if log_file.stat().st_mtime > time.time() - 86400:  # 24시간 이내
                recent_logs += 1
        
        activities.append({
            "type": "logging",
            "description": f"24시간 내 활성 로그 {recent_logs}개",
            "status": "normal" if recent_logs > 0 else "low"
        })
        
        return activities
    
    def generate_title(self, analysis_result: Dict[str, Any]) -> str:
        """분석 결과에 따른 동적 제목 생성"""
        status = analysis_result.get("status", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        status_titles = {
            "healthy": f"✅ VELOS 시스템 정상 운영 중 - {timestamp}",
            "warning": f"⚠️ VELOS 시스템 주의사항 발견 - {timestamp}", 
            "critical": f"🚨 VELOS 시스템 긴급 조치 필요 - {timestamp}",
            "error": f"❌ VELOS 시스템 모니터링 오류 - {timestamp}",
            "unknown": f"🔍 VELOS 시스템 상태 점검 - {timestamp}"
        }
        
        return status_titles.get(status, f"📊 VELOS 시스템 대시보드 - {timestamp}")
    
    def generate_dashboard_content(self) -> Dict[str, Any]:
        """전체 대시보드 콘텐츠 생성"""
        print("[INFO] 시스템 건강 상태 분석 중...")
        
        # 분석 실행
        integrity_analysis = self.analyze_system_integrity()
        performance_analysis = self.analyze_performance()
        recent_activities = self.get_recent_activities()
        
        # 제목 생성
        title = self.generate_title(integrity_analysis)
        
        # 요약 통계
        summary_stats = {
            "total_issues": len(integrity_analysis["critical_issues"]) + len(integrity_analysis["warnings"]),
            "critical_count": len(integrity_analysis["critical_issues"]),
            "warning_count": len(integrity_analysis["warnings"]),
            "db_records": integrity_analysis["metrics"].get("db_records", 0),
            "system_status": integrity_analysis["status"]
        }
        
        return {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "summary": summary_stats,
            "integrity": integrity_analysis,
            "performance": performance_analysis,
            "activities": recent_activities,
            "recommendations": integrity_analysis["recommendations"] + performance_analysis.get("optimizations", [])
        }

def generate_system_health_report() -> str:
    """시스템 건강 대시보드 보고서 생성"""
    analyzer = SystemHealthAnalyzer()
    dashboard_data = analyzer.generate_dashboard_content()
    
    # 마크다운 형식으로 보고서 생성
    report_lines = []
    
    # 제목
    report_lines.append(f"# {dashboard_data['title']}")
    report_lines.append("")
    
    # 요약 섹션
    summary = dashboard_data['summary']
    report_lines.append("## 📊 시스템 요약")
    report_lines.append(f"- **전체 상태**: {summary['system_status'].upper()}")
    report_lines.append(f"- **발견된 이슈**: {summary['total_issues']}건 (긴급 {summary['critical_count']}건, 주의 {summary['warning_count']}건)")
    report_lines.append(f"- **메모리 DB**: {summary['db_records']:,}개 레코드")
    report_lines.append("")
    
    # 긴급 이슈
    integrity = dashboard_data['integrity']
    if integrity['critical_issues']:
        report_lines.append("## 🚨 긴급 조치 필요")
        for issue in integrity['critical_issues']:
            report_lines.append(f"- {issue}")
        report_lines.append("")
    
    # 주의사항
    if integrity['warnings']:
        report_lines.append("## ⚠️ 주의사항")
        for warning in integrity['warnings']:
            report_lines.append(f"- {warning}")
        report_lines.append("")
    
    # 성능 분석
    performance = dashboard_data['performance']
    report_lines.append("## ⚡ 성능 상태")
    report_lines.append(f"- **메모리 효율성**: {performance['memory_efficiency']}")
    report_lines.append(f"- **I/O 성능**: {performance['io_performance']}")
    if performance['bottlenecks']:
        report_lines.append("### 병목 지점:")
        for bottleneck in performance['bottlenecks']:
            report_lines.append(f"  - {bottleneck}")
    report_lines.append("")
    
    # 최근 활동
    report_lines.append("## 🔄 최근 활동")
    for activity in dashboard_data['activities']:
        status_icon = "✅" if activity['status'] == 'normal' else "⚠️"
        report_lines.append(f"- {status_icon} {activity['description']}")
    report_lines.append("")
    
    # 권고사항
    if dashboard_data['recommendations']:
        report_lines.append("## 💡 권고사항")
        for rec in dashboard_data['recommendations']:
            report_lines.append(f"- {rec}")
        report_lines.append("")
    
    # 생성 정보
    report_lines.append("---")
    report_lines.append(f"*생성시간: {dashboard_data['timestamp']}*")
    report_lines.append("*VELOS 시스템 건강 대시보드 v1.0*")
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    report_content = generate_system_health_report()
    print(report_content)