"""
VELOS Memory Adapter Module

JSONL 버퍼와 SQLite 데이터베이스 간의 동기화를 처리하며,
실시간 데이터 수집과 지속적인 메모리 관리를 제공합니다.
"""

import json
import sqlite3
import uuid
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


class MemoryAdapterError(Exception):
    """Memory Adapter 관련 예외"""
    pass


class BufferError(MemoryAdapterError):
    """버퍼 관련 오류"""
    pass


class DatabaseError(MemoryAdapterError):
    """데이터베이스 관련 오류"""
    pass


class MemoryAdapter:
    """
    VELOS 메모리 어댑터
    
    JSONL 버퍼 → JSON → SQLite DB 동기화를 담당
    """
    
    def __init__(self, buffer_path: Path, db_path: Path, json_path: Path):
        """
        메모리 어댑터 초기화
        
        Args:
            buffer_path: JSONL 버퍼 파일 경로
            db_path: SQLite 데이터베이스 파일 경로
            json_path: JSON 메모리 파일 경로
        """
        self.buffer_path = buffer_path
        self.db_path = db_path
        self.json_path = json_path
        self._init_database()
    
    def _init_database(self) -> None:
        """데이터베이스 초기화 및 테이블 생성"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # memory 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memory_timestamp 
                    ON memory(timestamp DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memory_content 
                    ON memory(content)
                """)
                
                conn.commit()
        except Exception as e:
            raise DatabaseError(f"데이터베이스 초기화 실패: {e}")
    
    def append(self, data: Dict) -> str:
        """
        JSONL 버퍼에 새 데이터 추가
        
        Args:
            data: 저장할 데이터
            
        Returns:
            생성된 레코드 ID
        """
        try:
            record_id = str(uuid.uuid4())
            data['id'] = record_id
            data['timestamp'] = datetime.now().isoformat()
            
            # JSONL 버퍼에 추가
            with open(self.buffer_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            return record_id
        except Exception as e:
            raise BufferError(f"버퍼 추가 실패: {e}")
    
    def flush_jsonl_to_db(self) -> int:
        """
        JSONL 버퍼의 데이터를 SQLite DB로 이동
        
        Returns:
            처리된 레코드 수
        """
        if not self.buffer_path.exists():
            return 0
        
        try:
            processed = 0
            buffer_data = []
            
            # 버퍼 파일 읽기
            with open(self.buffer_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            buffer_data.append(data)
                        except json.JSONDecodeError as e:
                            print(f"JSONL 파싱 오류 무시: {e}")
                            continue
            
            if not buffer_data:
                return 0
            
            # DB에 저장
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for data in buffer_data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO memory (id, content, timestamp, metadata)
                        VALUES (?, ?, ?, ?)
                    """, (
                        data['id'],
                        data.get('body', data.get('content', '')),
                        data['timestamp'],
                        json.dumps(data.get('metadata', {}), ensure_ascii=False)
                    ))
                    processed += 1
                
                conn.commit()
            
            # 버퍼 파일 초기화
            self.buffer_path.write_text('', encoding='utf-8')
            
            return processed
        except Exception as e:
            raise DatabaseError(f"DB 동기화 실패: {e}")
    
    def flush_jsonl_to_json(self) -> int:
        """
        JSONL 버퍼의 데이터를 JSON 파일로 이동
        
        Returns:
            처리된 레코드 수
        """
        if not self.buffer_path.exists():
            return 0
        
        try:
            processed = 0
            buffer_data = []
            
            # 버퍼 파일 읽기
            with open(self.buffer_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            buffer_data.append(data)
                        except json.JSONDecodeError as e:
                            print(f"JSONL 파싱 오류 무시: {e}")
                            continue
            
            if not buffer_data:
                return 0
            
            # 기존 JSON 파일 읽기
            existing_data = []
            if self.json_path.exists():
                try:
                    with open(self.json_path, 'r', encoding='utf-8-sig') as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    # JSON 파일이 손상된 경우 빈 배열로 시작
                    existing_data = []
            
            # 새 데이터 추가
            for data in buffer_data:
                # VELOS 형식으로 변환
                velos_entry = {
                    "from": data.get("role", "user"),
                    "insight": data.get("body", data.get("content", "")),
                    "ts": data.get("timestamp", datetime.now().isoformat()),
                    "raw_message": data.get("body", data.get("content", "")),
                    "tags": data.get("tags", ["auto"]),
                    "id": data.get("id", str(uuid.uuid4()))
                }
                existing_data.append(velos_entry)
                processed += 1
            
            # JSON 파일 저장
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            # 버퍼 파일 초기화
            self.buffer_path.write_text('', encoding='utf-8')
            
            return processed
        except Exception as e:
            raise BufferError(f"JSON 동기화 실패: {e}")
    
    def recent(self, limit: int = 10) -> List[Dict]:
        """
        최신 N개의 메모리 항목 조회
        
        Args:
            limit: 조회할 항목 수
            
        Returns:
            최신 메모리 항목들
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, timestamp, metadata
                    FROM memory
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'content': row[1],
                        'timestamp': row[2],
                        'metadata': json.loads(row[3]) if row[3] else {}
                    })
                
                return results
        except Exception as e:
            raise DatabaseError(f"최신 데이터 조회 실패: {e}")
    
    def search(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        키워드 기반 메모리 검색
        
        Args:
            keyword: 검색 키워드
            limit: 최대 결과 수
            
        Returns:
            검색 결과
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, content, timestamp, metadata
                    FROM memory
                    WHERE content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (f'%{keyword}%', limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'content': row[1],
                        'timestamp': row[2],
                        'metadata': json.loads(row[3]) if row[3] else {}
                    })
                
                return results
        except Exception as e:
            raise DatabaseError(f"검색 실패: {e}")
    
    def get_stats(self) -> Dict:
        """
        메모리 통계 정보
        
        Returns:
            통계 정보 딕셔너리
        """
        try:
            stats = {
                'buffer_size': 0,
                'db_records': 0,
                'json_records': 0,
                'last_sync': None
            }
            
            # 버퍼 크기 확인
            if self.buffer_path.exists():
                with open(self.buffer_path, 'r', encoding='utf-8') as f:
                    stats['buffer_size'] = len([line for line in f if line.strip()])
            
            # DB 레코드 수 확인
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memory")
                stats['db_records'] = cursor.fetchone()[0]
                
                # 마지막 동기화 시간 확인
                cursor.execute("SELECT MAX(timestamp) FROM memory")
                result = cursor.fetchone()[0]
                stats['last_sync'] = result
            
            # JSON 레코드 수 확인
            if self.json_path.exists():
                try:
                    with open(self.json_path, 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                        stats['json_records'] = len(data)
                except json.JSONDecodeError:
                    stats['json_records'] = 0
            
            return stats
        except Exception as e:
            raise DatabaseError(f"통계 조회 실패: {e}")
    
    def cleanup_old_records(self, days: int = 30) -> int:
        """
        오래된 레코드 정리
        
        Args:
            days: 보관할 일수
            
        Returns:
            삭제된 레코드 수
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM memory 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except Exception as e:
            raise DatabaseError(f"정리 실패: {e}")
    
    def recover_from_backup(self, backup_path: Path) -> bool:
        """
        백업에서 복구
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            복구 성공 여부
        """
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, self.db_path)
                self._init_database()
                return True
            return False
        except Exception as e:
            raise DatabaseError(f"복구 실패: {e}")


def create_memory_adapter() -> MemoryAdapter:
    """
    기본 설정으로 메모리 어댑터 생성
    
    Returns:
        MemoryAdapter 인스턴스
    """
    from modules.report_paths import ROOT
    
    buffer_path = ROOT / "data" / "memory" / "memory_buffer.jsonl"
    db_path = ROOT / "data" / "memory" / "velos_memory.db"
    json_path = ROOT / "data" / "memory" / "learning_memory.json"
    
    return MemoryAdapter(buffer_path, db_path, json_path)


if __name__ == "__main__":
    # 테스트 코드
    adapter = create_memory_adapter()
    
    # 테스트 데이터 추가
    test_data = {
        "body": "테스트 메시지",
        "role": "user",
        "metadata": {"source": "test"}
    }
    
    record_id = adapter.append(test_data)
    print(f"추가된 레코드 ID: {record_id}")
    
    # 동기화
    processed = adapter.flush_jsonl_to_db()
    print(f"DB 동기화 완료: {processed}개 레코드")
    
    # 통계 확인
    stats = adapter.get_stats()
    print(f"메모리 통계: {stats}")
