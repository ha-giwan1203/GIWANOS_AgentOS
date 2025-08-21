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
VELOS GPT-5 Memory Integration Module

GPT-5와 VELOS 메모리 시스템의 완전한 통합을 담당하는 고수준 래퍼 모듈
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import asyncio
from threading import Lock

# VELOS 핵심 모듈들
try:
    from .gpt5_client import GPT5Client, GPT5Request, GPT5Response
    from .context_builder import ContextBuilder
    from .velos_chat_memory import VELOSChatMemory, get_chat_memory
    from .memory_adapter import MemoryAdapter
    from ..memory.advanced.memory_analytics import MemoryAnalytics
except ImportError as e:
    print(f"[WARNING] VELOS 모듈 import 실패: {e}")
    GPT5Client = None
    ContextBuilder = None
    VELOSChatMemory = None
    MemoryAdapter = None
    MemoryAnalytics = None


@dataclass
class VELOSMemoryContext:
    """VELOS 메모리 컨텍스트 정보"""
    recent_memories: List[Dict[str, Any]]
    relevant_memories: List[Dict[str, Any]]
    context_summary: str
    confidence_score: float
    total_memories_searched: int
    context_tokens: int


@dataclass
class VELOSGPTSession:
    """VELOS GPT-5 세션 정보"""
    session_id: str
    created_at: datetime
    total_interactions: int
    total_tokens_used: int
    total_cost: float
    context_length: int
    memory_integration_enabled: bool
    last_interaction: Optional[datetime] = None


class VELOSGPTMemoryIntegrator:
    """
    VELOS GPT-5 메모리 통합 관리자
    
    Features:
    - GPT-5와 메모리 시스템 완전 통합
    - 지능형 컨텍스트 구성
    - 자동 학습 및 패턴 인식
    - 비용 효율적인 메모리 활용
    - 다중 세션 관리
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        메모리 통합 관리자 초기화
        
        Args:
            session_id: 세션 ID (None이면 자동 생성)
        """
        # 핵심 컴포넌트 초기화
        self.gpt5_client = GPT5Client() if GPT5Client else None
        self.context_builder = ContextBuilder() if ContextBuilder else None
        self.chat_memory = get_chat_memory() if get_chat_memory else None
        self.memory_adapter = MemoryAdapter() if MemoryAdapter else None
        self.memory_analytics = MemoryAnalytics() if MemoryAnalytics else None
        
        if not self.gpt5_client:
            raise RuntimeError("GPT-5 클라이언트를 초기화할 수 없습니다.")
        
        # 세션 설정
        self.session_id = session_id or f"velos_gpt5_{int(time.time())}"
        self.session = VELOSGPTSession(
            session_id=self.session_id,
            created_at=datetime.now(),
            total_interactions=0,
            total_tokens_used=0,
            total_cost=0.0,
            context_length=20,  # 기본 컨텍스트 길이
            memory_integration_enabled=True
        )
        
        # 설정
        self.max_context_tokens = 8000  # GPT-5 컨텍스트 한계 고려
        self.memory_relevance_threshold = 0.3
        self.auto_save_interval = 5  # 5회 상호작용마다 자동 저장
        self._lock = Lock()
        
        # 로깅
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"VELOS GPT-5 메모리 통합 관리자 초기화: {self.session_id}")
    
    def _build_memory_context(self, user_message: str, 
                            context_length: int = None) -> VELOSMemoryContext:
        """
        사용자 메시지에 기반한 메모리 컨텍스트 구성
        
        Args:
            user_message: 사용자 메시지
            context_length: 컨텍스트 길이
        
        Returns:
            메모리 컨텍스트 객체
        """
        context_length = context_length or self.session.context_length
        
        try:
            # 최근 메모리 가져오기
            recent_memories = []
            if self.memory_adapter:
                recent_memories = self.memory_adapter.get_recent(limit=context_length)
            
            # 관련 메모리 검색
            relevant_memories = []
            if self.memory_adapter:
                search_results = self.memory_adapter.search(user_message, limit=10)
                relevant_memories = [
                    result for result in search_results 
                    if result.get('relevance_score', 0) >= self.memory_relevance_threshold
                ]
            
            # 컨텍스트 요약 생성
            context_summary = self._generate_context_summary(
                recent_memories, relevant_memories
            )
            
            # 신뢰도 점수 계산
            confidence_score = self._calculate_context_confidence(
                recent_memories, relevant_memories, user_message
            )
            
            # 토큰 수 추정
            context_tokens = self._estimate_context_tokens(
                recent_memories, relevant_memories, context_summary
            )
            
            return VELOSMemoryContext(
                recent_memories=recent_memories,
                relevant_memories=relevant_memories,
                context_summary=context_summary,
                confidence_score=confidence_score,
                total_memories_searched=len(recent_memories) + len(relevant_memories),
                context_tokens=context_tokens
            )
            
        except Exception as e:
            self.logger.error(f"메모리 컨텍스트 구성 실패: {str(e)}")
            return VELOSMemoryContext(
                recent_memories=[],
                relevant_memories=[],
                context_summary="메모리 컨텍스트를 구성할 수 없습니다.",
                confidence_score=0.0,
                total_memories_searched=0,
                context_tokens=0
            )
    
    def _generate_context_summary(self, recent_memories: List[Dict], 
                                relevant_memories: List[Dict]) -> str:
        """메모리 기반 컨텍스트 요약 생성"""
        if not recent_memories and not relevant_memories:
            return "이전 대화 기록이 없습니다."
        
        summary_parts = []
        
        if recent_memories:
            recent_topics = [mem.get('body', '')[:100] for mem in recent_memories[-3:]]
            summary_parts.append(f"최근 대화 주제: {', '.join(recent_topics)}")
        
        if relevant_memories:
            relevant_topics = [mem.get('body', '')[:100] for mem in relevant_memories[:3]]
            summary_parts.append(f"관련 과거 대화: {', '.join(relevant_topics)}")
        
        return " | ".join(summary_parts)
    
    def _calculate_context_confidence(self, recent_memories: List[Dict],
                                    relevant_memories: List[Dict],
                                    user_message: str) -> float:
        """컨텍스트 신뢰도 점수 계산"""
        score = 0.0
        
        # 최근 메모리 점수
        if recent_memories:
            score += 0.4 * min(len(recent_memories) / 10, 1.0)
        
        # 관련 메모리 점수
        if relevant_memories:
            avg_relevance = sum(
                mem.get('relevance_score', 0) for mem in relevant_memories
            ) / len(relevant_memories)
            score += 0.6 * avg_relevance
        
        return min(score, 1.0)
    
    def _estimate_context_tokens(self, recent_memories: List[Dict],
                               relevant_memories: List[Dict],
                               context_summary: str) -> int:
        """컨텍스트 토큰 수 추정"""
        total_chars = 0
        
        for memory in recent_memories:
            total_chars += len(memory.get('body', ''))
        
        for memory in relevant_memories:
            total_chars += len(memory.get('body', ''))
        
        total_chars += len(context_summary)
        
        # 대략적인 토큰 추정: 4 characters ≈ 1 token
        return total_chars // 4
    
    def _build_gpt5_messages(self, user_message: str, 
                           memory_context: VELOSMemoryContext) -> List[Dict[str, str]]:
        """GPT-5용 메시지 리스트 구성"""
        messages = []
        
        # 시스템 프롬프트 (VELOS 컨텍스트 포함)
        system_prompt = self._build_system_prompt(memory_context)
        messages.append({
            "role": "system", 
            "content": system_prompt
        })
        
        # 토큰 제한 내에서 이전 대화 추가
        available_tokens = self.max_context_tokens - len(system_prompt) // 4 - len(user_message) // 4 - 500  # 여유분
        current_tokens = 0
        
        # 최근 메모리부터 역순으로 추가
        for memory in reversed(memory_context.recent_memories):
            memory_content = memory.get('body', '')
            memory_tokens = len(memory_content) // 4
            
            if current_tokens + memory_tokens > available_tokens:
                break
            
            messages.append({
                "role": memory.get('role', 'user'),
                "content": memory_content
            })
            current_tokens += memory_tokens
        
        # 메시지 순서 복원
        messages = [messages[0]] + list(reversed(messages[1:]))
        
        # 현재 사용자 메시지 추가
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _build_system_prompt(self, memory_context: VELOSMemoryContext) -> str:
        """VELOS 시스템 프롬프트 구성"""
        base_prompt = """당신은 VELOS (GPT-5 기반 초고도화 AI 자동화 및 자가학습 시스템)입니다.

핵심 특징:
- GPT-5 최신 언어모델을 사용하여 고품질 응답 생성
- 완전한 외장메모리 시스템으로 모든 대화를 기억하고 학습
- 실시간 맥락 유지 및 지능형 컨텍스트 관리
- 사용자와의 모든 상호작용을 메모리에 저장하여 개인화된 경험 제공

현재 메모리 상태:"""
        
        memory_status = f"""
- 컨텍스트 신뢰도: {memory_context.confidence_score:.2f}
- 검색된 메모리: {memory_context.total_memories_searched}개
- 컨텍스트 요약: {memory_context.context_summary}
"""
        
        guidelines = """
응답 가이드라인:
1. 메모리 컨텍스트를 활용하여 개인화된 응답 제공
2. 이전 대화 내용을 자연스럽게 참조
3. 학습한 패턴과 선호사항을 반영
4. 정확하고 도움이 되는 정보 제공
5. 필요시 메모리 부족이나 불확실함을 솔직히 표현

이제 사용자의 메시지에 응답하세요."""
        
        return base_prompt + memory_status + guidelines
    
    async def generate_response_async(self, user_message: str,
                                    context_length: Optional[int] = None,
                                    **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        비동기 GPT-5 응답 생성 (메모리 통합)
        
        Args:
            user_message: 사용자 메시지
            context_length: 컨텍스트 길이
            **kwargs: 추가 GPT-5 파라미터
        
        Returns:
            (응답 텍스트, 메타데이터) 튜플
        """
        start_time = time.time()
        
        try:
            # 메모리 컨텍스트 구성
            memory_context = self._build_memory_context(user_message, context_length)
            
            # GPT-5 메시지 구성
            messages = self._build_gpt5_messages(user_message, memory_context)
            
            # GPT-5 요청 생성
            gpt5_request = GPT5Request(
                messages=messages,
                model=kwargs.get("model", "gpt-5"),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens"),
                metadata={
                    "session_id": self.session_id,
                    "memory_context": asdict(memory_context),
                    "velos_integration": True
                }
            )
            
            # GPT-5 응답 생성
            gpt5_response = await self.gpt5_client.generate_async(gpt5_request)
            
            # 채팅 메모리에 저장
            if self.chat_memory:
                self.chat_memory.add_message(user_message, "user", {
                    "session_id": self.session_id,
                    "timestamp": start_time
                })
                self.chat_memory.add_message(gpt5_response.content, "assistant", {
                    "session_id": self.session_id,
                    "model": "gpt-5",
                    "cost": gpt5_response.metadata.get("cost", 0),
                    "tokens": gpt5_response.usage.get("total_tokens", 0)
                })
            
            # 세션 통계 업데이트
            with self._lock:
                self.session.total_interactions += 1
                self.session.total_tokens_used += gpt5_response.usage.get("total_tokens", 0)
                self.session.total_cost += gpt5_response.metadata.get("cost", 0)
                self.session.last_interaction = datetime.now()
            
            # 메타데이터 구성
            response_metadata = {
                "session_id": self.session_id,
                "response_time": time.time() - start_time,
                "memory_context": asdict(memory_context),
                "tokens_used": gpt5_response.usage.get("total_tokens", 0),
                "estimated_cost": gpt5_response.metadata.get("cost", 0),
                "model": gpt5_response.model,
                "interaction_count": self.session.total_interactions
            }
            
            self.logger.info(f"GPT-5 응답 생성 완료: {self.session_id} "
                           f"(토큰: {gpt5_response.usage.get('total_tokens', 0)}, "
                           f"시간: {response_metadata['response_time']:.2f}초)")
            
            return gpt5_response.content, response_metadata
            
        except Exception as e:
            self.logger.error(f"GPT-5 응답 생성 실패: {str(e)}")
            error_response = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
            error_metadata = {
                "session_id": self.session_id,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            return error_response, error_metadata
    
    def generate_response(self, user_message: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        동기 GPT-5 응답 생성 (비동기 래퍼)
        
        Args:
            user_message: 사용자 메시지
            **kwargs: 추가 파라미터
        
        Returns:
            (응답 텍스트, 메타데이터) 튜플
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_response_async(user_message, **kwargs)
        )
    
    def chat(self, user_message: str, **kwargs) -> str:
        """
        간단한 채팅 인터페이스
        
        Args:
            user_message: 사용자 메시지
            **kwargs: 추가 파라미터
        
        Returns:
            GPT-5 응답 텍스트
        """
        response, _ = self.generate_response(user_message, **kwargs)
        return response
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        현재 세션 통계 반환
        
        Returns:
            세션 통계 정보
        """
        with self._lock:
            session_dict = asdict(self.session)
            session_dict["created_at"] = self.session.created_at.isoformat()
            session_dict["last_interaction"] = (
                self.session.last_interaction.isoformat() 
                if self.session.last_interaction else None
            )
            
            # GPT-5 클라이언트 통계 추가
            if self.gpt5_client:
                gpt5_stats = self.gpt5_client.get_statistics()
                session_dict["gpt5_client_stats"] = gpt5_stats
            
            return session_dict
    
    def get_memory_insights(self, days_back: int = 7) -> Dict[str, Any]:
        """
        메모리 기반 인사이트 생성
        
        Args:
            days_back: 분석할 일수
        
        Returns:
            메모리 인사이트
        """
        if not self.memory_analytics:
            return {"error": "메모리 분석 엔진을 사용할 수 없습니다."}
        
        try:
            insights = {
                "productivity_patterns": self.memory_analytics.analyze_productivity_patterns(days_back),
                "session_summary": self.get_session_statistics(),
                "generated_at": datetime.now().isoformat()
            }
            return insights
        except Exception as e:
            return {"error": f"인사이트 생성 실패: {str(e)}"}
    
    def export_session(self) -> Dict[str, Any]:
        """
        세션 데이터 내보내기
        
        Returns:
            세션 전체 데이터
        """
        export_data = {
            "session": self.get_session_statistics(),
            "chat_memory": None,
            "export_timestamp": datetime.now().isoformat()
        }
        
        # 채팅 메모리 내보내기
        if self.chat_memory:
            try:
                export_data["chat_memory"] = self.chat_memory.get_stats()
            except Exception as e:
                export_data["chat_memory_error"] = str(e)
        
        return export_data


# 전역 통합 관리자 인스턴스들
_session_managers: Dict[str, VELOSGPTMemoryIntegrator] = {}
_default_manager: Optional[VELOSGPTMemoryIntegrator] = None


def get_velos_gpt_manager(session_id: Optional[str] = None) -> VELOSGPTMemoryIntegrator:
    """
    VELOS GPT-5 메모리 통합 관리자 인스턴스 반환
    
    Args:
        session_id: 세션 ID (None이면 기본 관리자 반환)
    
    Returns:
        VELOSGPTMemoryIntegrator 인스턴스
    """
    global _session_managers, _default_manager
    
    if session_id is None:
        if _default_manager is None:
            _default_manager = VELOSGPTMemoryIntegrator()
        return _default_manager
    
    if session_id not in _session_managers:
        _session_managers[session_id] = VELOSGPTMemoryIntegrator(session_id)
    
    return _session_managers[session_id]


def chat_velos_gpt5(message: str, session_id: Optional[str] = None, **kwargs) -> str:
    """
    VELOS GPT-5 채팅 편의 함수
    
    Args:
        message: 사용자 메시지
        session_id: 세션 ID
        **kwargs: 추가 파라미터
    
    Returns:
        GPT-5 응답
    """
    manager = get_velos_gpt_manager(session_id)
    return manager.chat(message, **kwargs)


# 테스트 코드
if __name__ == "__main__":
    import asyncio
    
    async def test_velos_gpt_integration():
        """VELOS GPT-5 메모리 통합 테스트"""
        try:
            # 관리자 초기화
            manager = VELOSGPTMemoryIntegrator("test_session")
            
            # 테스트 대화
            messages = [
                "안녕하세요! VELOS 시스템에 대해 알려주세요.",
                "메모리 시스템은 어떻게 작동하나요?",
                "이전에 말했던 내용을 기억하고 있나요?"
            ]
            
            for i, message in enumerate(messages):
                print(f"\n--- 대화 {i+1} ---")
                print(f"사용자: {message}")
                
                response, metadata = manager.generate_response(message)
                print(f"VELOS: {response}")
                print(f"메타데이터: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
            
            # 세션 통계 확인
            print("\n--- 세션 통계 ---")
            stats = manager.get_session_statistics()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"테스트 실패: {e}")
    
    # 테스트 실행
    print("=== VELOS GPT-5 메모리 통합 테스트 ===")
    asyncio.run(test_velos_gpt_integration())