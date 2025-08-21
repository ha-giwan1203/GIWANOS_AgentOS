
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

{% if active_sessions -%}
| 세션 ID | 시작 시간 | 지속시간 | 메시지 수 | 맥락 점수 |
|---------|----------|----------|-----------|-----------|
{% for session in active_sessions -%}
| {{ session.session_id }} | {{ session.start_time.split('.')[0] }} | {{ session.get('duration_formatted', '0분') }} | {{ session.message_count }} | {{ "%.2f"|format(session.context_score) }} |
{% endfor %}
{% else -%}
*현재 활성 세션이 없습니다.*
{% endif -%}

## 💬 실시간 대화 요약

{% if conversation_summaries -%}
{% for summary in conversation_summaries -%}
### 🗣️ 세션 {{ summary.session_id[:8] }}...
- **상호작용 패턴**: {{ summary.interaction_pattern }}
- **메시지 수**: {{ summary.message_count }}개
- **주요 키워드**: {{ summary.topic_keywords[:5]|join(', ') if summary.topic_keywords else '분석 중...' }}
- **대화 내용**:
{{ summary.content_summary }}
- **품질 지표**: 일관성 {{ "%.2f"|format(summary.quality_metrics.get('response_consistency', 0) * 100) }}%, 
  주제 일관성 {{ "%.2f"|format(summary.quality_metrics.get('topic_coherence', 0) * 100) }}%

{% endfor %}
{% else -%}
*최근 1시간 내 대화 요약이 없습니다.*

### 📝 대화 요약 정보
- **요약 범위**: 최근 1시간 내 활성 세션
- **분석 내용**: 주요 키워드, 상호작용 패턴, 대화 품질
- **업데이트**: 실시간 자동 생성
{% endif -%}

## 🎯 주요 인사이트

{% if insights -%}
{% for insight in insights -%}
- {{ insight }}
{% endfor %}
{% else -%}
- 시스템이 정상적으로 작동하고 있습니다.
- 메모리 및 맥락 관리가 안정적입니다.
{% endif -%}

## ⚠️ 권장 사항

{% if recommendations -%}
{% for rec in recommendations -%}
- {{ rec }}
{% endfor %}
{% else -%}
- 현재 특별한 조치가 필요하지 않습니다.
- 정기적인 모니터링을 계속 유지하세요.
{% endif -%}

---
*이 보고서는 VELOS-GPT5 모니터링 시스템에서 자동 생성되었습니다.*
