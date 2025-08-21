# VELOS GPT-5 사용법 가이드

## 🎉 **GPT-5 업그레이드 완료!**

VELOS 시스템이 **GPT-5 기반**으로 성공적으로 업그레이드되었습니다.

---

## 📋 **업그레이드 내용**

### ✅ **완료된 작업**

1. **🔄 시스템 정체성 업데이트**
   - `data/memory/identity_memory.json`: GPT-4o → **GPT-5**
   - 버전: v2.0-stable → **v2.1-gpt5**

2. **🧠 GPT-5 클라이언트 모듈 생성**
   - `modules/core/gpt5_client.py`: 완전한 GPT-5 API 클라이언트
   - 비동기/동기 지원, 비용 추적, 캐시, 재시도 로직

3. **💾 메모리 통합 시스템**
   - `modules/core/velos_gpt5_memory.py`: GPT-5와 메모리 완전 통합
   - 지능형 컨텍스트 구성, 세션 관리, 자동 학습

4. **🛠️ 환경 설정 도구**
   - `scripts/setup_gpt5_environment.py`: 자동 환경 설정 및 검증
   - `scripts/test_gpt5_integration.py`: 종합 기능 테스트

---

## 🚀 **빠른 시작**

### 1️⃣ **환경 설정**

```bash
# 환경 설정 스크립트 실행
python scripts/setup_gpt5_environment.py

# 필요한 패키지 설치 (누락된 경우)
pip install openai>=1.0.0

# 환경변수 설정 (필수!)
export OPENAI_API_KEY="sk-your-gpt5-api-key-here"
```

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-your-gpt5-api-key-here"
```

### 2️⃣ **통합 테스트**

```bash
# 전체 시스템 테스트
python scripts/test_gpt5_integration.py
```

### 3️⃣ **GPT-5 사용 시작**

```python
# 간단한 GPT-5 채팅
from modules.core.velos_gpt5_memory import chat_velos_gpt5

response = chat_velos_gpt5("안녕하세요! GPT-5 시스템이 잘 작동하나요?")
print(response)
```

---

## 💻 **사용 방법**

### 🔥 **방법 1: 고급 메모리 통합 채팅**

```python
from modules.core.velos_gpt5_memory import VELOSGPTMemoryIntegrator

# 세션 기반 대화 (메모리 유지)
manager = VELOSGPTMemoryIntegrator("my_session")

# 메모리와 함께 대화
response = manager.chat("VELOS 시스템에 대해 설명해주세요")
print(response)

# 이전 대화를 기억하는 후속 질문
response = manager.chat("방금 설명한 내용 중에서 가장 중요한 특징은 뭔가요?")
print(response)

# 세션 통계 확인
stats = manager.get_session_statistics()
print(f"총 대화: {stats['total_interactions']}회")
print(f"사용 토큰: {stats['total_tokens_used']}개")
print(f"예상 비용: ${stats['total_cost']:.6f}")
```

### ⚡ **방법 2: 직접 GPT-5 클라이언트**

```python
from modules.core.gpt5_client import GPT5Client, GPT5Request

# 클라이언트 초기화
client = GPT5Client()

# 간단한 채팅
response_text = client.chat("GPT-5의 새로운 능력에 대해 알려주세요")
print(response_text)

# 상세한 요청
request = GPT5Request(
    messages=[
        {"role": "system", "content": "당신은 VELOS AI 어시스턴트입니다."},
        {"role": "user", "content": "외장메모리 시스템의 장점을 설명해주세요"}
    ],
    temperature=0.7,
    max_tokens=500
)

response = client.generate(request)
print(f"응답: {response.content}")
print(f"사용 토큰: {response.usage['total_tokens']}")
print(f"비용: ${response.metadata['cost']:.6f}")
```

### 🧠 **방법 3: 메모리 기반 컨텍스트 활용**

```python
from modules.core.velos_gpt5_memory import get_velos_gpt_manager

# 기본 관리자 가져오기
manager = get_velos_gpt_manager()

# 메모리 인사이트와 함께 대화
response, metadata = manager.generate_response(
    "최근 우리가 나눈 대화에서 어떤 패턴을 발견할 수 있나요?",
    context_length=20  # 최근 20개 메모리 참조
)

print(f"응답: {response}")
print(f"컨텍스트 신뢰도: {metadata['memory_context']['confidence_score']:.2f}")
print(f"참조 메모리: {metadata['memory_context']['total_memories_searched']}개")
```

---

## 🔧 **고급 기능**

### 📊 **비용 및 사용량 모니터링**

```python
from modules.core.gpt5_client import get_gpt5_client

client = get_gpt5_client()
stats = client.get_statistics()

print(f"총 요청: {stats['request_count']}회")
print(f"총 토큰: {stats['total_tokens_used']:,}개") 
print(f"총 비용: ${stats['total_cost']:.6f}")
print(f"요청당 평균 비용: ${stats['average_cost_per_request']:.6f}")
```

### 🧪 **시스템 헬스체크**

```python
from modules.core.gpt5_client import GPT5Client

client = GPT5Client()
health = client.health_check()

print("시스템 상태:", health['status'])
print("API 키 설정:", health['api_key_configured'])
print("메모리 어댑터:", health['memory_adapter_available'])
```

### 💾 **메모리 분석**

```python
from modules.core.velos_gpt5_memory import VELOSGPTMemoryIntegrator

manager = VELOSGPTMemoryIntegrator()
insights = manager.get_memory_insights(days_back=7)

print("지난 7일 메모리 인사이트:")
print(insights['productivity_patterns'])
```

---

## ⚙️ **설정 및 커스터마이징**

### 🎛️ **GPT-5 파라미터 조정**

```python
# 창의적 모드 (높은 temperature)
response = manager.chat(
    "창의적인 아이디어를 제안해주세요",
    temperature=1.0,
    max_tokens=800
)

# 정확한 모드 (낮은 temperature) 
response = manager.chat(
    "데이터 분석 결과를 요약해주세요",
    temperature=0.3,
    max_tokens=300
)
```

### 🔄 **캐시 관리**

```python
from modules.core.gpt5_client import get_gpt5_client

client = get_gpt5_client()

# 캐시 상태 확인
stats = client.get_statistics()
print("캐시 통계:", stats['cache_stats'])

# 캐시 초기화
client.clear_cache()
print("캐시가 초기화되었습니다")
```

---

## 🚨 **문제 해결**

### ❌ **자주 발생하는 오류**

1. **`OPENAI_API_KEY` 오류**
   ```bash
   # 해결: API 키 설정 확인
   echo $OPENAI_API_KEY  # Linux/Mac
   echo $env:OPENAI_API_KEY  # Windows PowerShell
   ```

2. **모듈 임포트 오류**
   ```bash
   # 해결: 환경 설정 스크립트 실행
   python scripts/setup_gpt5_environment.py
   ```

3. **GPT-5 모델 접근 오류**
   ```python
   # 해결: GPT-4로 대체 테스트
   from modules.core.gpt5_client import GPT5Request
   request = GPT5Request(
       messages=[{"role": "user", "content": "test"}],
       model="gpt-4"  # GPT-5 대신 GPT-4 사용
   )
   ```

### 🔍 **디버깅 도구**

```python
# 자세한 로깅 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# 테스트 실행
python scripts/test_gpt5_integration.py
```

---

## 📈 **성능 최적화 팁**

### ⚡ **응답 속도 향상**
- 컨텍스트 길이 조정: `context_length=10` (기본값: 20)
- 캐시 활용: 동일한 질문은 캐시에서 즉시 응답
- 비동기 호출 사용: 여러 요청 병렬 처리

### 💰 **비용 절약**
- `max_tokens` 설정으로 응답 길이 제한
- Temperature 낮춰서 일관된 응답 (캐시 효율 증대)
- 불필요한 컨텍스트 메모리 제한

### 🧠 **메모리 효율성**
- 정기적 메모리 정리: `chat_memory.clear_buffer()`
- 관련성 임계값 조정: `memory_relevance_threshold=0.5`

---

## 🎯 **다음 단계**

1. **API 키 발급**: OpenAI에서 GPT-5 API 키 발급
2. **환경 설정**: `setup_gpt5_environment.py` 실행
3. **테스트**: `test_gpt5_integration.py`로 시스템 검증
4. **실제 사용**: 위의 사용 방법으로 GPT-5 활용 시작

---

## 📞 **지원 및 문의**

- **환경 설정 문제**: `scripts/setup_gpt5_environment.py` 실행 후 결과 확인
- **기능 테스트**: `scripts/test_gpt5_integration.py`로 종합 진단
- **상세 로그**: `data/logs/gpt5_*.json` 파일 확인

---

**🎉 축하합니다! VELOS 시스템이 GPT-5로 성공적으로 업그레이드되었습니다!**

이제 최첨단 GPT-5의 능력과 VELOS의 완벽한 메모리 시스템을 함께 활용할 수 있습니다.