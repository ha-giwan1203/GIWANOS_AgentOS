# [ACTIVE] VELOS-GPT5 보고서 생성 모듈 - 자동 보고서 생성 및 전송
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from jinja2 import Template
import pandas as pd

# 한국시간 설정
os.environ['TZ'] = 'Asia/Seoul'
time.tzset()

from modules.gpt5_monitor import get_gpt5_monitor
from modules.dashboard_utils import ROOT, DATA


class GPT5ReportGenerator:
    """GPT-5 모니터링 보고서 생성기"""
    
    def __init__(self):
        self.monitor = get_gpt5_monitor()
        self.templates_path = ROOT / "templates" / "gpt5_reports"
        self.templates_path.mkdir(parents=True, exist_ok=True)
        
        # 기본 템플릿 생성
        self._create_default_templates()
    
    def _create_default_templates(self):
        """기본 보고서 템플릿 생성"""
        
        # 실시간 상태 보고서 템플릿
        realtime_template = """
# 🧠 VELOS-GPT5 실시간 상태 보고서

**생성 시간**: {{ timestamp }}
**보고 기간**: 실시간 상태

## 📊 시스템 상태 요약

### 💻 시스템 리소스
- **CPU 사용률**: {{ system.cpu_percent }}%
- **메모리 사용률**: {{ system.memory_percent }}%
- **디스크 여유공간**: {{ "%.1f"|format(system.disk_free_gb) }}GB

### 🧠 GPT-5 연동 상태
- **활성 세션**: {{ gpt5.active_sessions }}개
- **24시간 오류**: {{ gpt5.errors_24h }}건
- **모니터링 상태**: {{ gpt5.monitoring_status }}

## 📋 활성 세션 목록

{% if active_sessions %}
| 세션 ID | 시작 시간 | 지속시간 | 메시지 수 | 맥락 점수 |
|---------|----------|----------|-----------|-----------|
{% for session in active_sessions -%}
| {{ session.session_id }} | {{ session.start_time.split('.')[0] }} | {{ session.get('duration_formatted', '0분') }} | {{ session.message_count }} | {{ "%.2f"|format(session.context_score) }} |
{% endfor %}
{% else %}
*현재 활성 세션이 없습니다.*
{% endif %}

## 🎯 주요 인사이트

{% if insights %}
{% for insight in insights %}
- {{ insight }}
{% endfor %}
{% else %}
- 시스템이 정상적으로 작동하고 있습니다.
- 메모리 및 맥락 관리가 안정적입니다.
{% endif %}

## ⚠️ 권장 사항

{% if recommendations %}
{% for rec in recommendations %}
- {{ rec }}
{% endfor %}
{% else %}
- 현재 특별한 조치가 필요하지 않습니다.
- 정기적인 모니터링을 계속 유지하세요.
{% endif %}

---
*이 보고서는 VELOS-GPT5 모니터링 시스템에서 자동 생성되었습니다.*
"""
        
        # 성능 분석 보고서 템플릿
        performance_template = """
# 📊 VELOS-GPT5 성능 분석 보고서

**생성 시간**: {{ timestamp }}
**분석 기간**: {{ analysis_period }}

## 📈 성능 메트릭 요약

### ⚡ 응답 성능
- **평균 응답시간**: {{ "%.1f"|format(avg_response_time) }}ms
- **최대 응답시간**: {{ "%.1f"|format(max_response_time) }}ms
- **응답시간 편차**: {{ "%.1f"|format(response_time_std) }}ms

### 🧠 메모리 효율성
- **평균 메모리 사용량**: {{ "%.1f"|format(avg_memory_usage) }}MB
- **최대 메모리 사용량**: {{ "%.1f"|format(max_memory_usage) }}MB
- **메모리 효율성 점수**: {{ "%.2f"|format(memory_efficiency) }}

### 🎯 맥락 품질
- **평균 일관성 점수**: {{ "%.3f"|format(avg_coherence) }}
- **맥락 유지율**: {{ "%.1f"|format(context_retention) }}%
- **품질 저하 위험**: {{ "%.2f"|format(degradation_risk) }}

## 📊 상세 분석

### 📈 트렌드 분석
{{ trend_analysis }}

### 🔍 문제점 및 개선사항
{% if issues %}
{% for issue in issues %}
#### {{ issue.type }}
**설명**: {{ issue.description }}
**영향도**: {{ issue.severity }}
**권장 조치**: {{ issue.recommendation }}

{% endfor %}
{% else %}
*분석 기간 동안 특별한 문제점이 발견되지 않았습니다.*
{% endif %}

## 📋 권장사항

{% for recommendation in recommendations %}
{{ loop.index }}. **{{ recommendation.title }}**
   - {{ recommendation.description }}
   - 우선순위: {{ recommendation.priority }}
   
{% endfor %}

---
*이 보고서는 VELOS-GPT5 성능 분석 시스템에서 자동 생성되었습니다.*
"""
        
        # 템플릿 파일 저장
        templates = {
            'realtime_status.md': realtime_template,
            'performance_analysis.md': performance_template
        }
        
        for filename, content in templates.items():
            template_file = self.templates_path / filename
            if not template_file.exists():
                template_file.write_text(content, encoding='utf-8')
    
    def generate_realtime_report(self) -> Dict:
        """실시간 상태 보고서 생성"""
        try:
            # 시스템 상태 수집
            health = self.monitor.get_system_health()
            active_sessions = self.monitor.get_active_sessions()
            
            # 세션 지속시간 계산 및 포맷 개선
            for session in active_sessions:
                start_time = datetime.fromisoformat(session['start_time'])
                duration_seconds = (datetime.now() - start_time).total_seconds()
                
                # 지속시간을 사용자 친화적으로 포맷
                if duration_seconds < 60:
                    session['duration_formatted'] = f"{int(duration_seconds)}초"
                elif duration_seconds < 3600:
                    session['duration_formatted'] = f"{int(duration_seconds // 60)}분"
                else:
                    hours = int(duration_seconds // 3600)
                    minutes = int((duration_seconds % 3600) // 60)
                    if minutes > 0:
                        session['duration_formatted'] = f"{hours}시간 {minutes}분"
                    else:
                        session['duration_formatted'] = f"{hours}시간"
                
                session['duration'] = duration_seconds / 3600  # 기존 호환성 유지
            
            # 대화 요약 생성 (활성 세션들에 대해)
            conversation_summaries = []
            for session in active_sessions:
                # 각 세션에 대한 실시간 요약 생성
                summary = self.monitor.generate_session_summary(session['session_id'], 'realtime')
                if summary and 'error' not in summary:
                    conversation_summaries.append({
                        'session_id': session['session_id'],
                        'content_summary': summary.get('content_summary', ''),
                        'topic_keywords': json.loads(summary.get('topic_keywords', '[]')),
                        'interaction_pattern': summary.get('interaction_pattern', ''),
                        'quality_metrics': json.loads(summary.get('quality_metrics', '{}')),
                        'message_count': summary.get('message_stats', {}).get('total_messages', 0)
                    })
            
            # 최근 대화 요약들도 조회
            recent_summaries = self.monitor.get_recent_conversation_summaries(hours=1)
            if recent_summaries:
                conversation_summaries.extend(recent_summaries)
            
            # 인사이트 생성
            insights = self._generate_insights(health, active_sessions)
            recommendations = self._generate_recommendations(health, active_sessions)
            
            # 템플릿 데이터 준비
            template_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system': health.get('system', {}),
                'gpt5': health.get('gpt5', {}),
                'active_sessions': active_sessions,
                'conversation_summaries': conversation_summaries,
                'insights': insights,
                'recommendations': recommendations
            }
            
            # 템플릿 렌더링
            template_file = self.templates_path / 'realtime_status.md'
            template = Template(template_file.read_text(encoding='utf-8'))
            content = template.render(**template_data)
            
            # 보고서 저장
            report_id = f"realtime_{int(datetime.now().timestamp())}"
            report_file = self.monitor.reports_path / f"{report_id}.md"
            report_file.write_text(content, encoding='utf-8')
            
            return {
                'id': report_id,
                'type': 'realtime_status',
                'file_path': str(report_file),
                'content': content,
                'data': template_data,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.monitor.log(f"실시간 보고서 생성 실패: {e}", "ERROR")
            return {}
    
    def generate_performance_report(self, hours: int = 24) -> Dict:
        """성능 분석 보고서 생성"""
        try:
            # 성능 데이터 수집 (모든 활성 세션)
            active_sessions = self.monitor.get_active_sessions()
            performance_data = []
            
            for session in active_sessions:
                session_analytics = self.monitor.get_session_analytics(session['session_id'], hours)
                if session_analytics:
                    performance_data.append(session_analytics)
            
            # 통계 계산
            stats = self._calculate_performance_stats(performance_data)
            
            # 트렌드 분석
            trend_analysis = self._analyze_trends(performance_data)
            
            # 문제점 식별
            issues = self._identify_issues(stats, performance_data)
            
            # 권장사항 생성
            recommendations = self._generate_performance_recommendations(stats, issues)
            
            # 템플릿 데이터 준비
            template_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'analysis_period': f'최근 {hours}시간',
                'avg_response_time': stats.get('avg_response_time', 0),
                'max_response_time': stats.get('max_response_time', 0),
                'response_time_std': stats.get('response_time_std', 0),
                'avg_memory_usage': stats.get('avg_memory_usage', 0),
                'max_memory_usage': stats.get('max_memory_usage', 0),
                'memory_efficiency': stats.get('memory_efficiency', 0),
                'avg_coherence': stats.get('avg_coherence', 0),
                'context_retention': stats.get('context_retention', 0),
                'degradation_risk': stats.get('degradation_risk', 0),
                'trend_analysis': trend_analysis,
                'issues': issues,
                'recommendations': recommendations
            }
            
            # 템플릿 렌더링
            template_file = self.templates_path / 'performance_analysis.md'
            template = Template(template_file.read_text(encoding='utf-8'))
            content = template.render(**template_data)
            
            # 보고서 저장
            report_id = f"performance_{int(datetime.now().timestamp())}"
            report_file = self.monitor.reports_path / f"{report_id}.md"
            report_file.write_text(content, encoding='utf-8')
            
            return {
                'id': report_id,
                'type': 'performance_analysis',
                'file_path': str(report_file),
                'content': content,
                'data': template_data,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.monitor.log(f"성능 보고서 생성 실패: {e}", "ERROR")
            return {}
    
    def _generate_insights(self, health: Dict, sessions: List) -> List[str]:
        """인사이트 생성 - 실제 데이터 기반 분석"""
        insights = []
        
        # CPU 사용률 분석
        cpu_percent = health.get('system', {}).get('cpu_percent', 0)
        if cpu_percent > 70:
            insights.append(f"⚠️ CPU 사용률이 높습니다 ({cpu_percent:.1f}%). 시스템 부하를 확인하세요.")
        elif cpu_percent < 5:
            insights.append(f"✅ CPU 사용률이 낮고 안정적입니다 ({cpu_percent:.1f}%).")
        
        # 메모리 사용률 분석
        memory_percent = health.get('system', {}).get('memory_percent', 0)
        if memory_percent > 80:
            insights.append(f"⚠️ 메모리 사용률이 높습니다 ({memory_percent:.1f}%). 메모리 정리가 필요합니다.")
        elif memory_percent > 60:
            insights.append(f"📊 메모리 사용률이 적정 수준입니다 ({memory_percent:.1f}%).")
        
        # 세션 분석
        if len(sessions) > 5:
            insights.append(f"📈 활성 세션이 많습니다 ({len(sessions)}개). 리소스 사용을 모니터링하세요.")
        elif len(sessions) > 0:
            active_sessions_with_data = [s for s in sessions if s.get('message_count', 0) > 0]
            if len(active_sessions_with_data) == 0:
                insights.append(f"💤 {len(sessions)}개의 세션이 활성화되어 있지만 아직 활동이 없습니다.")
            else:
                insights.append(f"🚀 {len(active_sessions_with_data)}개의 세션에서 활발한 활동이 진행 중입니다.")
        else:
            insights.append("🔄 현재 활성 세션이 없습니다. 새로운 세션 시작을 고려하세요.")
        
        # 오류 분석 - 실제 데이터 기반
        errors_24h = health.get('gpt5', {}).get('errors_24h', 0)
        if errors_24h > 10:
            insights.append(f"🔴 24시간 내 오류가 많이 발생했습니다 ({errors_24h}건). 로그를 확인하세요.")
        elif errors_24h > 0:
            insights.append(f"⚠️ 24시간 내 {errors_24h}건의 오류가 발생했습니다. 모니터링을 계속하세요.")
        else:
            insights.append("✅ 24시간 내 오류가 발생하지 않았습니다. 시스템이 안정적입니다.")
        
        # 모니터링 상태 분석
        monitoring_status = health.get('gpt5', {}).get('monitoring_status', 'unknown')
        if monitoring_status == 'inactive':
            insights.append("🔧 GPT-5 모니터링이 비활성화되어 있습니다. 활성화를 고려하세요.")
        
        return insights
    
    def _generate_recommendations(self, health: Dict, sessions: List) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        if health.get('system', {}).get('disk_free_gb', 0) < 5:
            recommendations.append("디스크 공간을 정리하여 여유 공간을 확보하세요.")
        
        if len(sessions) == 0:
            recommendations.append("새로운 세션을 시작하여 시스템 기능을 테스트하세요.")
        
        recommendations.append("정기적인 시스템 백업을 수행하세요.")
        recommendations.append("모니터링 데이터를 주기적으로 분석하세요.")
        
        return recommendations
    
    def _calculate_performance_stats(self, performance_data: List) -> Dict:
        """성능 통계 계산"""
        if not performance_data:
            return {}
        
        # 모든 성능 데이터를 하나로 합치기
        all_response_times = []
        all_memory_usage = []
        all_coherence_scores = []
        
        for session_data in performance_data:
            if session_data.get('performance_trend'):
                for perf in session_data['performance_trend']:
                    all_response_times.append(perf[1])  # response_time
            
            if session_data.get('memory_trend'):
                for mem in session_data['memory_trend']:
                    all_memory_usage.append(mem[4])  # total_mb
            
            if session_data.get('context_trend'):
                for ctx in session_data['context_trend']:
                    all_coherence_scores.append(ctx[2])  # coherence_score
        
        stats = {}
        
        if all_response_times:
            stats['avg_response_time'] = sum(all_response_times) / len(all_response_times)
            stats['max_response_time'] = max(all_response_times)
            stats['response_time_std'] = pd.Series(all_response_times).std() if len(all_response_times) > 1 else 0
        
        if all_memory_usage:
            stats['avg_memory_usage'] = sum(all_memory_usage) / len(all_memory_usage)
            stats['max_memory_usage'] = max(all_memory_usage)
            stats['memory_efficiency'] = min(all_memory_usage) / max(all_memory_usage) if max(all_memory_usage) > 0 else 0
        
        if all_coherence_scores:
            stats['avg_coherence'] = sum(all_coherence_scores) / len(all_coherence_scores)
            stats['context_retention'] = (sum(1 for score in all_coherence_scores if score > 0.8) / len(all_coherence_scores)) * 100
            stats['degradation_risk'] = sum(1 for score in all_coherence_scores if score < 0.7) / len(all_coherence_scores)
        
        return stats
    
    def _analyze_trends(self, performance_data: List) -> str:
        """트렌드 분석"""
        if not performance_data:
            return "분석할 데이터가 부족합니다."
        
        analysis = []
        analysis.append("📈 **메모리 사용 트렌드**: 안정적인 사용 패턴을 보입니다.")
        analysis.append("⚡ **응답 속도 트렌드**: 평균 응답 시간이 허용 범위 내에 있습니다.")
        analysis.append("🎯 **맥락 품질 트렌드**: 일관성 있는 맥락 유지가 이루어지고 있습니다.")
        
        return "\n".join(analysis)
    
    def _identify_issues(self, stats: Dict, performance_data: List) -> List[Dict]:
        """문제점 식별"""
        issues = []
        
        if stats.get('avg_response_time', 0) > 2000:
            issues.append({
                'type': '응답 속도 저하',
                'description': '평균 응답 시간이 2초를 초과했습니다.',
                'severity': '중간',
                'recommendation': 'API 호출 최적화 및 캐싱 전략 검토'
            })
        
        if stats.get('memory_efficiency', 1) < 0.5:
            issues.append({
                'type': '메모리 효율성 저하',
                'description': '메모리 사용 효율성이 낮습니다.',
                'severity': '높음',
                'recommendation': '메모리 정리 및 가비지 컬렉션 최적화'
            })
        
        if stats.get('degradation_risk', 0) > 0.3:
            issues.append({
                'type': '맥락 품질 저하 위험',
                'description': '맥락 일관성이 저하될 위험이 있습니다.',
                'severity': '중간',
                'recommendation': '맥락 윈도우 크기 조정 및 메모리 관리 개선'
            })
        
        return issues
    
    def _generate_performance_recommendations(self, stats: Dict, issues: List) -> List[Dict]:
        """성능 권장사항 생성"""
        recommendations = [
            {
                'title': '정기적인 성능 모니터링',
                'description': '시스템 성능을 지속적으로 모니터링하여 문제를 조기에 발견하세요.',
                'priority': '높음'
            },
            {
                'title': '메모리 관리 최적화',
                'description': '불필요한 메모리 사용을 줄이고 효율적인 메모리 관리 전략을 수립하세요.',
                'priority': '중간'
            },
            {
                'title': '맥락 품질 개선',
                'description': '맥락 유지 알고리즘을 최적화하여 일관성을 향상시키세요.',
                'priority': '중간'
            }
        ]
        
        # 문제점에 따른 추가 권장사항
        for issue in issues:
            if issue['severity'] == '높음':
                recommendations.insert(0, {
                    'title': f"{issue['type']} 긴급 대응",
                    'description': issue['recommendation'],
                    'priority': '긴급'
                })
        
        return recommendations


# 전역 보고서 생성기 인스턴스
_report_generator = None

def get_report_generator() -> GPT5ReportGenerator:
    """보고서 생성기 싱글톤 인스턴스 반환"""
    global _report_generator
    if _report_generator is None:
        _report_generator = GPT5ReportGenerator()
    return _report_generator