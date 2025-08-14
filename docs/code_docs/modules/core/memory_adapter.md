# Memory Adapter Module

## 개요

Memory Adapter는 VELOS 시스템의 메모리 관리를 담당하는 핵심 모듈입니다. JSONL 버퍼와 SQLite 데이터베이스 간의 동기화를 처리하며, 실시간 데이터 수집과 지속적인 메모리 관리를 제공합니다.

**위치**: `modules/core/memory_adapter.py` (구현 예정)

## 설계 목표

1. **실시간 데이터 수집**: JSONL 버퍼를 통한 빠른 데이터 수집
2. **지속적 저장**: SQLite DB를 통한 안정적인 데이터 저장
3. **효율적 검색**: 키워드 기반 검색 및 최신 데이터 조회
4. **자동 동기화**: 주기적인 JSONL → DB 변환

## 아키텍처 설계

### 메모리 계층 구조
```
┌─────────────────┐
│   JSONL Buffer  │ ← 실시간 데이터 수집
│ (memory_buffer) │
└─────────┬───────┘
          │ flush
          ▼
┌─────────────────┐
│ Learning Memory │ ← 중간 저장소
│   (JSON)        │
└─────────┬───────┘
          │ sync
          ▼
┌─────────────────┐
│  SQLite DB      │ ← 영구 저장소
│ (velos_memory)  │
└─────────────────┘
```

### 데이터 흐름
1. **수집**: 실시간 데이터 → JSONL 버퍼
2. **Flush**: JSONL → JSON 변환 (주기적)
3. **동기화**: JSON → SQLite 저장
4. **백업**: SQLite → 스냅샷 생성

## 클래스 설계

### MemoryAdapter 클래스

```python
class MemoryAdapter:
    def __init__(self, buffer_path: Path, db_path: Path, json_path: Path):
        self.buffer_path = buffer_path
        self.db_path = db_path
        self.json_path = json_path
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        pass
    
    def append(self, data: dict) -> str:
        """JSONL 버퍼에 새 데이터 추가"""
        pass
    
    def flush_jsonl_to_db(self) -> int:
        """JSONL 버퍼를 DB로 동기화"""
        pass
    
    def recent(self, limit: int = 10) -> List[dict]:
        """최신 N개 데이터 조회"""
        pass
    
    def search(self, keyword: str, limit: int = 50) -> List[dict]:
        """키워드 기반 검색"""
        pass
    
    def get_stats(self) -> dict:
        """메모리 통계 정보"""
        pass
```

## 주요 메서드 상세

### append()
**목적**: 실시간 데이터를 JSONL 버퍼에 추가

**매개변수**:
- `data` (dict): 저장할 데이터

**반환값**:
- `str`: 생성된 레코드 ID

**구현 예시**:
```python
def append(self, data: dict) -> str:
    record_id = str(uuid.uuid4())
    data['id'] = record_id
    data['timestamp'] = datetime.now().isoformat()
    
    with open(self.buffer_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    return record_id
```

### flush_jsonl_to_db()
**목적**: JSONL 버퍼의 데이터를 SQLite DB로 이동

**반환값**:
- `int`: 처리된 레코드 수

**구현 예시**:
```python
def flush_jsonl_to_db(self) -> int:
    if not self.buffer_path.exists():
        return 0
    
    processed = 0
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        
        with open(self.buffer_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    cursor.execute("""
                        INSERT INTO memory (id, content, timestamp, metadata)
                        VALUES (?, ?, ?, ?)
                    """, (data['id'], data['content'], data['timestamp'], 
                          json.dumps(data.get('metadata', {}))))
                    processed += 1
        
        conn.commit()
    
    # 버퍼 파일 초기화
    self.buffer_path.write_text('', encoding='utf-8')
    return processed
```

### recent()
**목적**: 최신 N개의 메모리 항목 조회

**매개변수**:
- `limit` (int): 조회할 항목 수 (기본값: 10)

**반환값**:
- `List[dict]`: 최신 메모리 항목들

**구현 예시**:
```python
def recent(self, limit: int = 10) -> List[dict]:
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
```

### search()
**목적**: 키워드 기반 메모리 검색

**매개변수**:
- `keyword` (str): 검색 키워드
- `limit` (int): 최대 결과 수 (기본값: 50)

**반환값**:
- `List[dict]`: 검색 결과

**구현 예시**:
```python
def search(self, keyword: str, limit: int = 50) -> List[dict]:
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
```

## 데이터베이스 스키마

### memory 테이블
```sql
CREATE TABLE memory (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memory_timestamp ON memory(timestamp DESC);
CREATE INDEX idx_memory_content ON memory(content);
```

### 메타데이터 구조
```json
{
  "source": "user_input",
  "type": "conversation",
  "tags": ["important", "followup"],
  "priority": "high",
  "user_id": "user123"
}
```

## 사용 예시

### 기본 사용법
```python
from modules.core.memory_adapter import MemoryAdapter
from pathlib import Path

# 어댑터 초기화
adapter = MemoryAdapter(
    buffer_path=Path("data/memory/memory_buffer.jsonl"),
    db_path=Path("data/memory/velos_memory.db"),
    json_path=Path("data/memory/learning_memory.json")
)

# 데이터 추가
record_id = adapter.append({
    "content": "사용자 질문: 시스템 상태는?",
    "metadata": {"source": "user", "type": "question"}
})

# 주기적 동기화
processed = adapter.flush_jsonl_to_db()
print(f"동기화 완료: {processed}개 레코드")

# 최신 데이터 조회
recent_data = adapter.recent(limit=5)
for item in recent_data:
    print(f"[{item['timestamp']}] {item['content']}")

# 키워드 검색
search_results = adapter.search("시스템")
for item in search_results:
    print(f"검색 결과: {item['content']}")
```

### 마스터 루프 통합
```python
# run_giwanos_master_loop.py에 통합
def main():
    adapter = MemoryAdapter(...)
    
    # 루프 시작 시 동기화
    adapter.flush_jsonl_to_db()
    
    # 최신 컨텍스트 로드
    recent_context = adapter.recent(limit=10)
    
    # 시스템 프롬프트에 컨텍스트 추가
    context_text = "\n".join([item['content'] for item in recent_context])
    
    # ... 기존 로직 ...
```

## 성능 최적화

### 인덱싱 전략
1. **타임스탬프 인덱스**: 최신 데이터 조회 최적화
2. **컨텐츠 인덱스**: 키워드 검색 최적화
3. **메타데이터 인덱스**: 필터링 최적화

### 배치 처리
```python
def batch_append(self, data_list: List[dict]) -> List[str]:
    """여러 데이터를 한 번에 추가"""
    record_ids = []
    with open(self.buffer_path, 'a', encoding='utf-8') as f:
        for data in data_list:
            record_id = str(uuid.uuid4())
            data['id'] = record_id
            data['timestamp'] = datetime.now().isoformat()
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
            record_ids.append(record_id)
    return record_ids
```

### 메모리 최적화
```python
def cleanup_old_records(self, days: int = 30):
    """오래된 레코드 정리"""
    cutoff_date = datetime.now() - timedelta(days=days)
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM memory 
            WHERE timestamp < ?
        """, (cutoff_date.isoformat(),))
        conn.commit()
```

## 오류 처리

### 예외 처리
```python
class MemoryAdapterError(Exception):
    """Memory Adapter 관련 예외"""
    pass

class BufferError(MemoryAdapterError):
    """버퍼 관련 오류"""
    pass

class DatabaseError(MemoryAdapterError):
    """데이터베이스 관련 오류"""
    pass
```

### 복구 메커니즘
```python
def recover_from_backup(self, backup_path: Path):
    """백업에서 복구"""
    if backup_path.exists():
        shutil.copy2(backup_path, self.db_path)
        self._init_database()
```

## 테스트

### 단위 테스트
```python
def test_append_and_flush():
    adapter = MemoryAdapter(...)
    
    # 데이터 추가
    record_id = adapter.append({"content": "test"})
    assert record_id is not None
    
    # 동기화
    processed = adapter.flush_jsonl_to_db()
    assert processed == 1
    
    # 검증
    recent = adapter.recent(limit=1)
    assert len(recent) == 1
    assert recent[0]['content'] == "test"
```

### 성능 테스트
```python
def test_performance():
    adapter = MemoryAdapter(...)
    
    # 대량 데이터 추가 테스트
    start_time = time.time()
    for i in range(1000):
        adapter.append({"content": f"test data {i}"})
    
    flush_time = time.time()
    adapter.flush_jsonl_to_db()
    end_time = time.time()
    
    print(f"추가 시간: {flush_time - start_time:.2f}초")
    print(f"동기화 시간: {end_time - flush_time:.2f}초")
```

## 향후 확장 계획

### 벡터 검색
```python
def vector_search(self, query_vector: List[float], limit: int = 10):
    """벡터 기반 유사도 검색"""
    # 향후 구현 예정
    pass
```

### 실시간 동기화
```python
def enable_realtime_sync(self):
    """실시간 동기화 활성화"""
    # 백그라운드 스레드로 주기적 동기화
    pass
```

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-08-14  
**작성자**: VELOS Development Team
