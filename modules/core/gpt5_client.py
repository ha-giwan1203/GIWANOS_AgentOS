# =========================================================
# VELOS 운영 철학 선언문
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
VELOS GPT-5 Client Module

GPT-5 API와의 안전한 통신 및 메모리 연동을 담당하는 핵심 클라이언트 모듈
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import asyncio
from threading import Lock

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI library not available. Install with: pip install openai")

# VELOS 메모리 시스템 연동
try:
    from .memory_adapter import MemoryAdapter
    from ..memory.cache.memory_cache import TTLCache
    from .logger_config import get_logger
except ImportError:
    MemoryAdapter = None
    TTLCache = None
    get_logger = None


@dataclass
class GPT5Response:
    """GPT-5 응답 데이터 구조"""
    content: str
    model: str
    usage: Dict[str, Any]
    timestamp: float
    request_id: str
    metadata: Dict[str, Any]


@dataclass
class GPT5Request:
    """GPT-5 요청 데이터 구조"""
    messages: List[Dict[str, str]]
    model: str = "gpt-5"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    metadata: Dict[str, Any] = None


class GPT5Client:
    """
    VELOS GPT-5 클라이언트
    
    Features:
    - GPT-5 API 통신
    - 자동 메모리 저장
    - 에러 복구 및 재시도
    - 비용 추적
    - 컨텍스트 관리
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        GPT-5 클라이언트 초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경변수 사용)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI 라이브러리가 설치되지 않았습니다.")
        
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=self.api_key)
        
        # 메모리 시스템 연동
        self.memory_adapter = MemoryAdapter() if MemoryAdapter else None
        self.cache = TTLCache(maxsize=100, ttl=3600) if TTLCache else None  # 1시간 TTL
        
        # 로깅 설정
        self.logger = get_logger(__name__) if get_logger else logging.getLogger(__name__)
        
        # 통계 및 설정
        self.request_count = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.max_retries = 3
        self.retry_delay = 1.0
        self._lock = Lock()
        
        self.logger.info("GPT-5 클라이언트 초기화 완료")
    
    def _generate_request_id(self) -> str:
        """요청 ID 생성"""
        return f"gpt5_req_{int(time.time() * 1000)}"
    
    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """
        토큰 사용량 기반 비용 계산 (GPT-5 예상 가격)
        
        Args:
            usage: OpenAI 사용량 정보
        
        Returns:
            예상 비용 (USD)
        """
        # GPT-5 예상 가격 (실제 가격은 OpenAI 공식 발표 후 업데이트 필요)
        # 임시 가격: GPT-4 Turbo의 2배로 가정
        input_cost_per_token = 0.00002  # $0.02/1K tokens
        output_cost_per_token = 0.00006  # $0.06/1K tokens
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        cost = (prompt_tokens * input_cost_per_token + 
                completion_tokens * output_cost_per_token)
        
        return cost
    
    async def generate_async(self, request: GPT5Request) -> GPT5Response:
        """
        비동기 GPT-5 응답 생성
        
        Args:
            request: GPT-5 요청 객체
        
        Returns:
            GPT-5 응답 객체
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        # 캐시 확인
        cache_key = json.dumps(request.messages, sort_keys=True)
        if self.cache:
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self.logger.info(f"캐시에서 응답 반환: {request_id}")
                return cached_response
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"GPT-5 API 호출 시작: {request_id} (시도 {attempt + 1})")
                
                # OpenAI API 호출
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=request.model,
                    messages=request.messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=request.stream
                )
                
                # 응답 처리
                content = response.choices[0].message.content
                usage = response.usage._asdict() if response.usage else {}
                
                # 비용 계산
                cost = self._calculate_cost(usage)
                
                # GPT5Response 객체 생성
                gpt5_response = GPT5Response(
                    content=content,
                    model=response.model,
                    usage=usage,
                    timestamp=start_time,
                    request_id=request_id,
                    metadata={
                        "cost": cost,
                        "attempt": attempt + 1,
                        "duration": time.time() - start_time,
                        **(request.metadata or {})
                    }
                )
                
                # 통계 업데이트
                with self._lock:
                    self.request_count += 1
                    self.total_tokens_used += usage.get("total_tokens", 0)
                    self.total_cost += cost
                
                # 캐시 저장
                if self.cache:
                    self.cache.set(cache_key, gpt5_response)
                
                # 메모리에 저장
                await self._save_to_memory(request, gpt5_response)
                
                self.logger.info(f"GPT-5 응답 성공: {request_id} (토큰: {usage.get('total_tokens', 0)}, 비용: ${cost:.6f})")
                
                return gpt5_response
                
            except Exception as e:
                self.logger.error(f"GPT-5 API 호출 실패: {request_id} (시도 {attempt + 1}): {str(e)}")
                
                if attempt == self.max_retries - 1:
                    raise Exception(f"GPT-5 API 호출 최종 실패: {str(e)}")
                
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 지수 백오프
    
    def generate(self, request: GPT5Request) -> GPT5Response:
        """
        동기 GPT-5 응답 생성 (비동기 래퍼)
        
        Args:
            request: GPT-5 요청 객체
        
        Returns:
            GPT-5 응답 객체
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.generate_async(request))
    
    async def _save_to_memory(self, request: GPT5Request, response: GPT5Response):
        """대화를 메모리에 저장"""
        if not self.memory_adapter:
            return
        
        try:
            # 사용자 메시지 저장
            user_message = request.messages[-1]  # 마지막 메시지가 사용자 메시지
            await asyncio.to_thread(
                self.memory_adapter.append,
                {
                    "body": user_message.get("content", ""),
                    "role": "user",
                    "metadata": {
                        "request_id": response.request_id,
                        "timestamp": response.timestamp,
                        "model": request.model,
                        **(request.metadata or {})
                    }
                }
            )
            
            # GPT-5 응답 저장
            await asyncio.to_thread(
                self.memory_adapter.append,
                {
                    "body": response.content,
                    "role": "assistant",
                    "metadata": {
                        "request_id": response.request_id,
                        "timestamp": response.timestamp,
                        "model": response.model,
                        "usage": response.usage,
                        "cost": response.metadata.get("cost", 0),
                        "duration": response.metadata.get("duration", 0),
                        **(request.metadata or {})
                    }
                }
            )
            
            self.logger.debug(f"메모리 저장 완료: {response.request_id}")
            
        except Exception as e:
            self.logger.error(f"메모리 저장 실패: {response.request_id}: {str(e)}")
    
    def chat(self, message: str, context: Optional[List[Dict[str, str]]] = None, 
             **kwargs) -> str:
        """
        간단한 채팅 인터페이스
        
        Args:
            message: 사용자 메시지
            context: 이전 대화 컨텍스트
            **kwargs: 추가 GPT-5 파라미터
        
        Returns:
            GPT-5 응답 텍스트
        """
        messages = context or []
        messages.append({"role": "user", "content": message})
        
        request = GPT5Request(
            messages=messages,
            model=kwargs.get("model", "gpt-5"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
            metadata=kwargs.get("metadata")
        )
        
        response = self.generate(request)
        return response.content
    
    def chat_with_memory(self, message: str, context_length: int = 10, **kwargs) -> str:
        """
        메모리 기반 채팅 (이전 대화 자동 로드)
        
        Args:
            message: 사용자 메시지
            context_length: 로드할 이전 대화 개수
            **kwargs: 추가 GPT-5 파라미터
        
Returns:
            GPT-5 응답 텍스트
        """
        context = []
        
        # 메모리에서 이전 대화 로드
        if self.memory_adapter:
            try:
                recent_memories = self.memory_adapter.get_recent(limit=context_length * 2)
                for memory in recent_memories:
                    role = memory.get("role", "user")
                    content = memory.get("body", "")
                    if content.strip():
                        context.append({"role": role, "content": content})
                
                # 컨텍스트 길이 제한
                context = context[-context_length:]
                
            except Exception as e:
                self.logger.error(f"메모리 컨텍스트 로드 실패: {str(e)}")
        
        return self.chat(message, context, **kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        클라이언트 사용 통계 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        with self._lock:
            return {
                "request_count": self.request_count,
                "total_tokens_used": self.total_tokens_used,
                "total_cost": self.total_cost,
                "average_cost_per_request": (
                    self.total_cost / self.request_count if self.request_count > 0 else 0
                ),
                "cache_stats": self.cache.get_stats() if self.cache else None,
                "model": "gpt-5",
                "client_uptime": time.time() - getattr(self, "_start_time", time.time())
            }
    
    def clear_cache(self):
        """캐시 초기화"""
        if self.cache:
            self.cache.clear()
            self.logger.info("GPT-5 클라이언트 캐시 초기화 완료")
    
    def health_check(self) -> Dict[str, Any]:
        """
        클라이언트 상태 확인
        
        Returns:
            헬스체크 결과
        """
        status = {
            "status": "healthy",
            "api_key_configured": bool(self.api_key),
            "memory_adapter_available": bool(self.memory_adapter),
            "cache_available": bool(self.cache),
            "openai_library_available": OPENAI_AVAILABLE,
            "last_check": datetime.now().isoformat()
        }
        
        # 간단한 API 테스트 (옵션)
        try:
            test_request = GPT5Request(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            # 실제 API 호출하지 않고 객체만 생성하여 검증
            status["request_validation"] = "passed"
        except Exception as e:
            status["status"] = "warning"
            status["request_validation"] = f"failed: {str(e)}"
        
        return status


# 전역 클라이언트 인스턴스
_global_gpt5_client = None


def get_gpt5_client() -> GPT5Client:
    """
    전역 GPT-5 클라이언트 인스턴스 반환
    
    Returns:
        GPT5Client 인스턴스
    """
    global _global_gpt5_client
    if _global_gpt5_client is None:
        _global_gpt5_client = GPT5Client()
    return _global_gpt5_client


def chat_gpt5(message: str, **kwargs) -> str:
    """
    GPT-5 채팅 편의 함수
    
    Args:
        message: 사용자 메시지
        **kwargs: 추가 파라미터
    
    Returns:
        GPT-5 응답
    """
    client = get_gpt5_client()
    return client.chat_with_memory(message, **kwargs)


# 테스트 및 예제 코드
if __name__ == "__main__":
    import asyncio
    
    async def test_gpt5_client():
        """GPT-5 클라이언트 테스트"""
        try:
            client = GPT5Client()
            
            # 헬스체크
            health = client.health_check()
            print("헬스체크:", json.dumps(health, indent=2, ensure_ascii=False))
            
            # 간단한 채팅 테스트
            response = client.chat("안녕하세요! VELOS 시스템에 대해 간단히 설명해주세요.")
            print("GPT-5 응답:", response)
            
            # 통계 확인
            stats = client.get_statistics()
            print("클라이언트 통계:", json.dumps(stats, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"테스트 실패: {e}")
    
    # 테스트 실행
    print("=== VELOS GPT-5 클라이언트 테스트 ===")
    asyncio.run(test_gpt5_client())