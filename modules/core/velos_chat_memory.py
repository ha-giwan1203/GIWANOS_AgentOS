# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:\giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
"""
VELOS Chat Memory Module

실시간 대화 내용을 자동으로 저장하고 관리하는 모듈입니다.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from modules.core.memory_adapter import MemoryAdapter


class VELOSChatMemory:
    """
    VELOS 실시간 채팅 메모리 관리자

    대화 내용을 실시간으로 저장하고 관리합니다.
    """

    def __init__(self):
        """채팅 메모리 초기화"""
        self.memory_adapter = MemoryAdapter()
        self.chat_buffer = []
        self.buffer_lock = Lock()
        self.auto_save_interval = 10  # 10개 메시지마다 자동 저장
        self.max_buffer_size = 100

    def add_message(self, message: str, role: str = "user", metadata: Optional[Dict] = None) -> str:
        """
        새 메시지 추가

        Args:
            message: 메시지 내용
            role: 발신자 역할 (user, assistant, system)
            metadata: 추가 메타데이터

        Returns:
            메시지 ID
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        chat_entry = {
            "id": message_id,
            "message": message,
            "role": role,
            "timestamp": timestamp,
            "metadata": metadata or {},
        }

        with self.buffer_lock:
            self.chat_buffer.append(chat_entry)

            # 버퍼 크기 제한
            if len(self.chat_buffer) > self.max_buffer_size:
                self.chat_buffer = self.chat_buffer[-self.max_buffer_size :]

            # 자동 저장 조건 확인
            if len(self.chat_buffer) >= self.auto_save_interval:
                self._auto_save()

        return message_id

    def add_conversation(self, conversation: List[Dict]) -> List[str]:
        """
        대화 세션 전체 추가

        Args:
            conversation: 대화 세션 리스트

        Returns:
            메시지 ID 리스트
        """
        message_ids = []

        for entry in conversation:
            message_id = self.add_message(
                message=entry.get("message", ""),
                role=entry.get("role", "user"),
                metadata=entry.get("metadata", {}),
            )
            message_ids.append(message_id)

        return message_ids

    def _auto_save(self) -> None:
        """자동 저장 실행"""
        try:
            with self.buffer_lock:
                if not self.chat_buffer:
                    return

                # 메모리 어댑터에 저장
                for entry in self.chat_buffer:
                    self.memory_adapter.append(
                        {
                            "body": entry["message"],
                            "role": entry["role"],
                            "metadata": {
                                **entry["metadata"],
                                "chat_id": entry["id"],
                                "timestamp": entry["timestamp"],
                            },
                        }
                    )

                # 버퍼 초기화
                self.chat_buffer.clear()

        except Exception as e:
            print(f"자동 저장 실패: {e}")

    def save_now(self) -> int:
        """
        즉시 저장 실행

        Returns:
            저장된 메시지 수
        """
        with self.buffer_lock:
            if not self.chat_buffer:
                return 0

            saved_count = len(self.chat_buffer)
            self._auto_save()
            return saved_count

    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """
        최근 메시지 조회

        Args:
            limit: 조회할 메시지 수

        Returns:
            최근 메시지 리스트
        """
        with self.buffer_lock:
            return self.chat_buffer[-limit:] if self.chat_buffer else []

    def search_messages(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        메시지 검색

        Args:
            keyword: 검색 키워드
            limit: 최대 결과 수

        Returns:
            검색 결과
        """
        # 메모리 어댑터에서 검색
        results = self.memory_adapter.search(keyword, limit)

        # 현재 버퍼에서도 검색
        with self.buffer_lock:
            buffer_results = [
                entry for entry in self.chat_buffer if keyword.lower() in entry["message"].lower()
            ]

        # 결과 병합 및 정렬
        all_results = results + buffer_results
        all_results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return all_results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """
        채팅 메모리 통계

        Returns:
            통계 정보
        """
        with self.buffer_lock:
            buffer_size = len(self.chat_buffer)

        memory_stats = self.memory_adapter.get_stats()

        return {
            "buffer_size": buffer_size,
            "memory_stats": memory_stats,
            "auto_save_interval": self.auto_save_interval,
            "max_buffer_size": self.max_buffer_size,
        }

    def clear_buffer(self) -> int:
        """
        버퍼 초기화

        Returns:
            초기화된 메시지 수
        """
        with self.buffer_lock:
            cleared_count = len(self.chat_buffer)
            self.chat_buffer.clear()
            return cleared_count

    def export_conversation(self, format: str = "json") -> str:
        """
        대화 내용 내보내기

        Args:
            format: 내보내기 형식 (json, txt)

        Returns:
            내보낸 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            file_path = f"data/memory/conversation_export_{timestamp}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.chat_buffer, f, ensure_ascii=False, indent=2)
        elif format == "txt":
            file_path = f"data/memory/conversation_export_{timestamp}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                for entry in self.chat_buffer:
                    f.write(f"[{entry['timestamp']}] {entry['role']}: {entry['message']}\n")
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")

        return file_path


# 전역 채팅 메모리 인스턴스
_global_chat_memory = None


def get_chat_memory() -> VELOSChatMemory:
    """
    전역 채팅 메모리 인스턴스 반환

    Returns:
        VELOSChatMemory 인스턴스
    """
    global _global_chat_memory
    if _global_chat_memory is None:
        _global_chat_memory = VELOSChatMemory()
    return _global_chat_memory


def add_chat_message(message: str, role: str = "user", metadata: Optional[Dict] = None) -> str:
    """
    채팅 메시지 추가 (편의 함수)

    Args:
        message: 메시지 내용
        role: 발신자 역할
        metadata: 추가 메타데이터

    Returns:
        메시지 ID
    """
    chat_memory = get_chat_memory()
    return chat_memory.add_message(message, role, metadata)


def save_chat_memory() -> int:
    """
    채팅 메모리 즉시 저장 (편의 함수)

    Returns:
        저장된 메시지 수
    """
    chat_memory = get_chat_memory()
    return chat_memory.save_now()


if __name__ == "__main__":
    # 테스트 코드
    chat_memory = get_chat_memory()

    # 테스트 메시지 추가
    chat_memory.add_message("안녕하세요! VELOS 시스템입니다.", "system")
    chat_memory.add_message("실시간 대화 저장 테스트입니다.", "user")
    chat_memory.add_message("테스트가 성공적으로 완료되었습니다.", "assistant")

    # 즉시 저장
    saved_count = chat_memory.save_now()
    print(f"저장된 메시지: {saved_count}개")

    # 통계 확인
    stats = chat_memory.get_stats()
    print(f"채팅 메모리 통계: {stats}")
