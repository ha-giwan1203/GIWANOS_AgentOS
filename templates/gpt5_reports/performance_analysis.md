
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
