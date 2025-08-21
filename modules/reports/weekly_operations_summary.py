#!/usr/bin/env python3
# =========================================================
# VELOS 주간 운영 요약 보고서 생성기
# 일주일간의 시스템 변화와 성과 분석
# =========================================================

import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

# Use correct path for sandbox environment  
ROOT = Path("/home/user/webapp")

class WeeklyOperationsAnalyzer:
    """주간 운영 분석기"""
    
    def __init__(self, weeks_back: int = 1):
        self.root = ROOT
        self.logs_dir = self.root / "data" / "logs"
        self.memory_dir = self.root / "data" / "memory"
        self.reports_dir = self.root / "data" / "reports"
        self.weeks_back = weeks_back
        
        # 시간 범위 설정
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=7 * weeks_back)
        
    def load_json_safe(self, file_path: Path) -> Dict[str, Any]:
        """안전한 JSON 로딩"""
        if not file_path.exists():
            return {}
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] JSON 로딩 실패 {file_path}: {e}")
            return {}
    
    def analyze_memory_growth(self) -> Dict[str, Any]:
        """메모리 데이터 증가 분석"""
        memory_analysis = {
            "total_records": 0,
            "growth_rate": "unknown",
            "activity_pattern": {},
            "top_topics": [],
            "insights": []
        }
        
        # 현재 메모리 상태
        health_data = self.load_json_safe(self.logs_dir / "system_health.json")
        current_records = health_data.get("memory_tick_stats", {}).get("db_records", 0)
        memory_analysis["total_records"] = current_records
        
        # 메모리 파일 분석
        memory_file = self.memory_dir / "autosave_inbox.jsonl"
        if memory_file.exists():
            try:
                lines = memory_file.read_text(encoding="utf-8").strip().split('\n')
                valid_entries = []
                topic_counter = Counter()
                
                for line in lines:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            valid_entries.append(entry)
                            
                            # 주제 분석 (태그나 내용에서)
                            tags = entry.get("tags", [])
                            raw_content = entry.get("raw", "").lower()
                            
                            for tag in tags:
                                topic_counter[tag] += 1
                            
                            # 키워드 추출
                            keywords = ["gpt", "slack", "memory", "report", "system", "api", "error", "test"]
                            for keyword in keywords:
                                if keyword in raw_content:
                                    topic_counter[keyword] += 1
                                    
                        except json.JSONDecodeError:
                            continue
                
                memory_analysis["activity_pattern"]["recent_entries"] = len(valid_entries)
                memory_analysis["top_topics"] = topic_counter.most_common(5)
                
                if len(valid_entries) > 0:
                    memory_analysis["insights"].append(f"📈 주간 새로운 학습 항목: {len(valid_entries)}건")
                    
                    if topic_counter:
                        top_topic = topic_counter.most_common(1)[0]
                        memory_analysis["insights"].append(f"🔥 가장 활발한 주제: {top_topic[0]} ({top_topic[1]}건)")
            except Exception as e:
                memory_analysis["insights"].append(f"⚠️ 메모리 분석 중 오류: {str(e)}")
        
        return memory_analysis
    
    def analyze_system_stability(self) -> Dict[str, Any]:
        """시스템 안정성 분석"""
        stability = {
            "uptime_score": "unknown",
            "error_incidents": [],
            "recovery_actions": [],
            "stability_trend": "stable",
            "recommendations": []
        }
        
        health_data = self.load_json_safe(self.logs_dir / "system_health.json")
        
        # 시스템 무결성 히스토리
        if health_data:
            # 현재 이슈 분석
            sys_integrity = health_data.get("system_integrity", {})
            if not sys_integrity.get("integrity_ok", True):
                issues = sys_integrity.get("details", {}).get("process_issues", [])
                for issue in issues:
                    stability["error_incidents"].append({
                        "type": "process_failure",
                        "description": issue,
                        "severity": "high" if "autosave" in issue else "medium"
                    })
                    
                    if "autosave" in issue:
                        stability["recovery_actions"].append("autosave_runner 재시작 필요")
            
            # 스냅샷 상태
            if health_data.get("snapshot_integrity_ok"):
                stability["recovery_actions"].append("백업 시스템 정상 작동 중")
            
            # 메모리 파이프라인 상태
            pipeline_ok = health_data.get("memory_pipeline_last_test_ok", False)
            if pipeline_ok:
                stability["uptime_score"] = "양호"
            else:
                stability["error_incidents"].append({
                    "type": "pipeline_failure", 
                    "description": "메모리 파이프라인 테스트 실패",
                    "severity": "medium"
                })
        
        # 안정성 평가
        error_count = len(stability["error_incidents"])
        if error_count == 0:
            stability["stability_trend"] = "매우 안정"
            stability["recommendations"].append("✅ 시스템 안정성 우수 - 현 상태 유지")
        elif error_count <= 2:
            stability["stability_trend"] = "주의 관찰"
            stability["recommendations"].append("⚠️ 소규모 이슈 발견 - 정기 점검 권장")
        else:
            stability["stability_trend"] = "불안정"
            stability["recommendations"].append("🚨 다수 이슈 발견 - 즉시 점검 필요")
        
        return stability
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        performance = {
            "response_efficiency": "unknown",
            "resource_utilization": "unknown", 
            "bottleneck_analysis": [],
            "optimization_opportunities": [],
            "weekly_summary": {}
        }
        
        health_data = self.load_json_safe(self.logs_dir / "system_health.json")
        
        if health_data:
            # 메모리 효율성
            memory_stats = health_data.get("memory_tick_stats", {})
            db_records = memory_stats.get("db_records", 0)
            
            if db_records > 0:
                if db_records < 500:
                    performance["resource_utilization"] = "경량"
                elif db_records < 1500:
                    performance["resource_utilization"] = "적정"
                else:
                    performance["resource_utilization"] = "높음"
                    performance["optimization_opportunities"].append(
                        f"메모리 레코드 {db_records:,}개 - 아카이빙 권장"
                    )
            
            # 핫버퍼 성능
            if health_data.get("hotbuf_ok"):
                rebuild_count = health_data.get("hotbuf_rebuild_count", 0)
                performance["response_efficiency"] = "정상"
                
                if rebuild_count > 30:
                    performance["bottleneck_analysis"].append(
                        f"핫버퍼 재빌드 빈번함 ({rebuild_count}회) - TTL 최적화 필요"
                    )
            
            # 디스패치 성능
            if health_data.get("dispatch_last_ok"):
                targets = health_data.get("dispatch_last_targets", [])
                performance["weekly_summary"]["dispatch_channels"] = len(targets)
                performance["optimization_opportunities"].append(
                    f"✅ {len(targets)}개 채널 디스패치 정상 작동"
                )
        
        return performance
        
    def generate_weekly_insights(self) -> List[str]:
        """주간 인사이트 생성"""
        insights = []
        
        # 시간 기반 인사이트
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:
            insights.append("📅 업무시간 중 보고서 생성 - 시스템 활성 상태")
        else:
            insights.append("🌙 업무외시간 보고서 생성 - 자동화 시스템 작동")
        
        # 데이터 기반 인사이트
        health_data = self.load_json_safe(self.logs_dir / "system_health.json")
        if health_data:
            session_count = health_data.get("session_bootstrap_count", 0)
            if session_count > 300:
                insights.append(f"🚀 높은 세션 활동 ({session_count}회) - 시스템 활발히 사용 중")
            
            last_flush_moved = health_data.get("last_flush_moved", 0)
            if last_flush_moved > 500:
                insights.append(f"💾 대량 데이터 플러시 ({last_flush_moved}건) - 활발한 학습 활동")
        
        return insights
    
    def generate_title(self, analysis_results: Dict[str, Any]) -> str:
        """분석 결과에 따른 동적 제목 생성"""
        week_period = f"{self.start_date.strftime('%m/%d')}-{self.end_date.strftime('%m/%d')}"
        
        # 안정성 기반 제목 결정
        stability = analysis_results.get("stability", {})
        trend = stability.get("stability_trend", "unknown")
        
        title_templates = {
            "매우 안정": f"✅ VELOS 주간 운영 보고서 - 안정적 운영 ({week_period})",
            "주의 관찰": f"⚠️ VELOS 주간 운영 보고서 - 주의사항 포함 ({week_period})",
            "불안정": f"🚨 VELOS 주간 운영 보고서 - 개선 필요 ({week_period})",
            "unknown": f"📊 VELOS 주간 운영 보고서 ({week_period})"
        }
        
        return title_templates.get(trend, title_templates["unknown"])
    
    def generate_weekly_content(self) -> Dict[str, Any]:
        """전체 주간 보고서 콘텐츠 생성"""
        print(f"[INFO] {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')} 주간 분석 중...")
        
        # 분석 실행
        memory_analysis = self.analyze_memory_growth()
        stability_analysis = self.analyze_system_stability()
        performance_analysis = self.analyze_performance_trends()
        weekly_insights = self.generate_weekly_insights()
        
        analysis_results = {
            "memory": memory_analysis,
            "stability": stability_analysis,
            "performance": performance_analysis
        }
        
        # 제목 생성
        title = self.generate_title(analysis_results)
        
        # 종합 평가
        overall_score = self.calculate_overall_score(analysis_results)
        
        return {
            "title": title,
            "period": f"{self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}",
            "timestamp": datetime.now().isoformat(),
            "overall_score": overall_score,
            "memory": memory_analysis,
            "stability": stability_analysis,
            "performance": performance_analysis,
            "insights": weekly_insights,
            "next_week_actions": self.generate_action_items(analysis_results)
        }
    
    def calculate_overall_score(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """종합 점수 계산"""
        score = {
            "stability": 0,
            "performance": 0,
            "growth": 0,
            "overall": "B",
            "summary": ""
        }
        
        # 안정성 점수
        stability = analysis_results["stability"]
        error_count = len(stability["error_incidents"])
        if error_count == 0:
            score["stability"] = 95
        elif error_count <= 2:
            score["stability"] = 75
        else:
            score["stability"] = 50
        
        # 성능 점수  
        performance = analysis_results["performance"]
        if performance["response_efficiency"] == "정상":
            score["performance"] = 90
        else:
            score["performance"] = 60
            
        # 성장 점수
        memory = analysis_results["memory"]
        if memory["total_records"] > 1000:
            score["growth"] = 85
        elif memory["total_records"] > 500:
            score["growth"] = 70
        else:
            score["growth"] = 50
        
        # 종합 평가
        avg_score = (score["stability"] + score["performance"] + score["growth"]) / 3
        if avg_score >= 90:
            score["overall"] = "A+"
        elif avg_score >= 80:
            score["overall"] = "A"
        elif avg_score >= 70:
            score["overall"] = "B+"
        elif avg_score >= 60:
            score["overall"] = "B"
        else:
            score["overall"] = "C"
            
        score["summary"] = f"안정성 {score['stability']}점, 성능 {score['performance']}점, 성장 {score['growth']}점"
        
        return score
    
    def generate_action_items(self, analysis_results: Dict[str, Any]) -> List[str]:
        """다음 주 액션 아이템 생성"""
        actions = []
        
        # 안정성 기반 액션
        stability = analysis_results["stability"]
        for action in stability["recommendations"]:
            actions.append(action)
        
        # 성능 기반 액션
        performance = analysis_results["performance"]
        for opportunity in performance["optimization_opportunities"]:
            if "권장" in opportunity or "필요" in opportunity:
                actions.append(f"🎯 {opportunity}")
        
        # 기본 액션들
        if not actions:
            actions.append("✅ 현재 상태 모니터링 지속")
            actions.append("📊 다음 주 성능 지표 수집")
        
        return actions

def generate_weekly_operations_report(weeks_back: int = 1) -> str:
    """주간 운영 요약 보고서 생성"""
    analyzer = WeeklyOperationsAnalyzer(weeks_back)
    report_data = analyzer.generate_weekly_content()
    
    # 마크다운 형식으로 보고서 생성
    report_lines = []
    
    # 제목 및 기간
    report_lines.append(f"# {report_data['title']}")
    report_lines.append(f"**분석 기간**: {report_data['period']}")
    report_lines.append("")
    
    # 종합 평가
    overall = report_data['overall_score']
    report_lines.append("## 🎯 종합 평가")
    report_lines.append(f"**종합 등급**: {overall['overall']}")
    report_lines.append(f"**상세 점수**: {overall['summary']}")
    report_lines.append("")
    
    # 메모리 & 학습 현황
    memory = report_data['memory']
    report_lines.append("## 🧠 메모리 & 학습 현황")
    report_lines.append(f"- **총 메모리 레코드**: {memory['total_records']:,}개")
    report_lines.append(f"- **주간 활동**: {memory['activity_pattern'].get('recent_entries', 0)}건")
    
    if memory['top_topics']:
        report_lines.append("- **주요 학습 주제**:")
        for topic, count in memory['top_topics']:
            report_lines.append(f"  - {topic}: {count}건")
    
    for insight in memory['insights']:
        report_lines.append(f"- {insight}")
    report_lines.append("")
    
    # 시스템 안정성
    stability = report_data['stability']
    report_lines.append("## 🛡️ 시스템 안정성")
    report_lines.append(f"- **안정성 평가**: {stability['stability_trend']}")
    report_lines.append(f"- **가동 시간**: {stability['uptime_score']}")
    
    if stability['error_incidents']:
        report_lines.append("- **발견된 이슈**:")
        for incident in stability['error_incidents']:
            severity_icon = "🚨" if incident['severity'] == 'high' else "⚠️"
            report_lines.append(f"  - {severity_icon} {incident['description']}")
    
    if stability['recovery_actions']:
        report_lines.append("- **복구 조치**:")
        for action in stability['recovery_actions']:
            report_lines.append(f"  - {action}")
    report_lines.append("")
    
    # 성능 분석
    performance = report_data['performance']
    report_lines.append("## ⚡ 성능 분석")
    report_lines.append(f"- **응답 효율성**: {performance['response_efficiency']}")
    report_lines.append(f"- **리소스 활용도**: {performance['resource_utilization']}")
    
    if performance['bottleneck_analysis']:
        report_lines.append("- **병목 지점**:")
        for bottleneck in performance['bottleneck_analysis']:
            report_lines.append(f"  - ⚠️ {bottleneck}")
    
    if performance['optimization_opportunities']:
        report_lines.append("- **최적화 기회**:")
        for opportunity in performance['optimization_opportunities']:
            report_lines.append(f"  - {opportunity}")
    report_lines.append("")
    
    # 주간 인사이트
    if report_data['insights']:
        report_lines.append("## 💡 주간 인사이트")
        for insight in report_data['insights']:
            report_lines.append(f"- {insight}")
        report_lines.append("")
    
    # 다음 주 액션 플랜
    report_lines.append("## 🎯 다음 주 액션 플랜")
    for action in report_data['next_week_actions']:
        report_lines.append(f"- {action}")
    report_lines.append("")
    
    # 생성 정보
    report_lines.append("---")
    report_lines.append(f"*생성시간: {report_data['timestamp']}*")
    report_lines.append("*VELOS 주간 운영 요약 보고서 v1.0*")
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    report_content = generate_weekly_operations_report()
    print(report_content)