# [ACTIVE] VELOS-GPT5 통합 모니터링 모듈 - GPT5 연동 메모리/맥락 추적
import json
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import psutil

from modules.dashboard_utils import ROOT, DATA, LOGS
from modules.monitor_utils import _safe_attach
from modules.timezone_utils import ensure_korean_timezone, get_korean_now, get_korean_timestamp, validate_timezone_consistency


class GPT5Monitor:
    """GPT-5 연동 상태 모니터링 및 성능 추적"""
    
    def __init__(self):
        # 한국시간 안정성 보장
        ensure_korean_timezone()
        
        self.root = ROOT
        self.data_path = DATA / "gpt5_monitor"
        self.sessions_path = self.data_path / "sessions"
        self.reports_path = self.data_path / "reports"
        self.logs_path = self.data_path / "logs"
        
        # 디렉토리 생성
        for path in [self.data_path, self.sessions_path, self.reports_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_path / "gpt5_monitor.db"
        self.init_database()
        
        # 모니터링 상태
        self.monitoring = False
        self.check_interval = 10  # 10초마다 체크
        
        # 한국시간 로깅 설정
        import logging
        self.logger = logging.getLogger('GPT5Monitor')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s KST] [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            # 한국시간으로 포매터 시간 설정
            formatter.converter = lambda *args: get_korean_now().timetuple()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
    def init_database(self):
        """GPT-5 모니터링 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # 세션 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gpt5_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    message_count INTEGER DEFAULT 0,
                    memory_usage_mb REAL DEFAULT 0,
                    context_score REAL DEFAULT 0,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # 메모리 상태 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    short_term_usage REAL,
                    long_term_usage REAL,
                    buffer_usage REAL,
                    total_memory_mb REAL,
                    FOREIGN KEY (session_id) REFERENCES gpt5_sessions(session_id)
                )
            """)
            
            # 맥락 추적 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context_windows INTEGER,
                    coherence_score REAL,
                    context_length INTEGER,
                    degradation_risk REAL,
                    FOREIGN KEY (session_id) REFERENCES gpt5_sessions(session_id)
                )
            """)
            
            # 성능 메트릭 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time_ms INTEGER,
                    tokens_processed INTEGER,
                    api_calls_count INTEGER,
                    error_count INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES gpt5_sessions(session_id)
                )
            """)
            
            # 대화 메시지 테이블 (대화 요약용)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_type TEXT,  -- 'user', 'assistant', 'system'
                    content TEXT,
                    tokens INTEGER DEFAULT 0,
                    context_used TEXT,  -- JSON format
                    FOREIGN KEY (session_id) REFERENCES gpt5_sessions(session_id)
                )
            """)
            
            # 세션 요약 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    summary_type TEXT,  -- 'hourly', 'session_end', 'realtime'
                    topic_keywords TEXT,  -- 주요 키워드들 (JSON)
                    content_summary TEXT,  -- 대화 내용 요약
                    interaction_pattern TEXT,  -- 상호작용 패턴
                    quality_metrics TEXT,  -- 품질 지표 (JSON)
                    FOREIGN KEY (session_id) REFERENCES gpt5_sessions(session_id)
                )
            """)
            
            # 보고서 전송 로그 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_transmissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT,
                    report_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    recipient TEXT,
                    transmission_method TEXT,
                    status TEXT,
                    file_path TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def log(self, message: str, level: str = "INFO"):
        """로깅 함수"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] GPT5Monitor: {message}"
        print(log_message)
        
        # 로그 파일에 기록
        log_file = self.logs_path / "gpt5_monitor.log"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception:
            pass
    
    def start_session(self, session_id: str) -> bool:
        """새 GPT-5 세션 시작"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO gpt5_sessions 
                (session_id, start_time, status) 
                VALUES (?, ?, 'active')
            """, (session_id, datetime.now()))
            
            conn.commit()
            conn.close()
            
            self.log(f"새 세션 시작: {session_id}")
            return True
            
        except Exception as e:
            self.log(f"세션 시작 실패: {e}", "ERROR")
            return False
    
    def end_session(self, session_id: str) -> bool:
        """GPT-5 세션 종료"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 세션 정보 조회
            cursor.execute("""
                SELECT start_time, message_count 
                FROM gpt5_sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            result = cursor.fetchone()
            if result:
                start_time = datetime.fromisoformat(result[0])
                duration = (datetime.now() - start_time).total_seconds()
                
                cursor.execute("""
                    UPDATE gpt5_sessions 
                    SET end_time = ?, duration_seconds = ?, status = 'completed'
                    WHERE session_id = ?
                """, (datetime.now(), duration, session_id))
                
                conn.commit()
                self.log(f"세션 종료: {session_id} (지속시간: {duration:.1f}초)")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"세션 종료 실패: {e}", "ERROR")
            return False
    
    def record_memory_state(self, session_id: str, memory_data: Dict) -> bool:
        """메모리 상태 기록 및 세션 메타데이터 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 메모리 상태 기록
            cursor.execute("""
                INSERT INTO memory_states 
                (session_id, short_term_usage, long_term_usage, buffer_usage, total_memory_mb)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                memory_data.get('short_term', 0),
                memory_data.get('long_term', 0),
                memory_data.get('buffer', 0),
                memory_data.get('total_mb', 0)
            ))
            
            # 세션 테이블의 메모리 사용량 업데이트
            cursor.execute("""
                UPDATE gpt5_sessions 
                SET memory_usage_mb = ?
                WHERE session_id = ?
            """, (memory_data.get('total_mb', 0), session_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"메모리 상태 기록 실패: {e}", "ERROR")
            return False
    
    def record_context_state(self, session_id: str, context_data: Dict) -> bool:
        """맥락 상태 기록 및 세션 맥락 점수 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 맥락 상태 기록
            cursor.execute("""
                INSERT INTO context_tracking 
                (session_id, context_windows, coherence_score, context_length, degradation_risk)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                context_data.get('windows', 0),
                context_data.get('coherence_score', 0),
                context_data.get('context_length', 0),
                context_data.get('degradation_risk', 0)
            ))
            
            # 세션 테이블의 맥락 점수 업데이트
            cursor.execute("""
                UPDATE gpt5_sessions 
                SET context_score = ?
                WHERE session_id = ?
            """, (context_data.get('coherence_score', 0), session_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"맥락 상태 기록 실패: {e}", "ERROR")
            return False
    
    def record_performance(self, session_id: str, perf_data: Dict) -> bool:
        """성능 메트릭 기록 및 세션 메시지 카운트 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 성능 메트릭 기록
            cursor.execute("""
                INSERT INTO performance_metrics 
                (session_id, response_time_ms, tokens_processed, api_calls_count, error_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                perf_data.get('response_time_ms', 0),
                perf_data.get('tokens_processed', 0),
                perf_data.get('api_calls', 0),
                perf_data.get('errors', 0)
            ))
            
            # 세션 테이블의 메시지 카운트 증가
            cursor.execute("""
                UPDATE gpt5_sessions 
                SET message_count = message_count + ?
                WHERE session_id = ?
            """, (perf_data.get('api_calls', 1), session_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"성능 메트릭 기록 실패: {e}", "ERROR")
            return False
    
    def get_active_sessions(self) -> List[Dict]:
        """활성 세션 목록 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, start_time, message_count, memory_usage_mb, context_score
                FROM gpt5_sessions 
                WHERE status = 'active'
                ORDER BY start_time DESC
            """)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'start_time': row[1],
                    'message_count': row[2],
                    'memory_usage_mb': row[3],
                    'context_score': row[4]
                })
            
            conn.close()
            return sessions
            
        except Exception as e:
            self.log(f"활성 세션 조회 실패: {e}", "ERROR")
            return []
    
    def get_session_analytics(self, session_id: str, hours: int = 24) -> Dict:
        """세션별 분석 데이터 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            
            # 메모리 트렌드
            cursor.execute("""
                SELECT timestamp, short_term_usage, long_term_usage, buffer_usage, total_memory_mb
                FROM memory_states 
                WHERE session_id = ? AND timestamp > ?
                ORDER BY timestamp
            """, (session_id, since))
            
            memory_data = cursor.fetchall()
            
            # 맥락 트렌드
            cursor.execute("""
                SELECT timestamp, context_windows, coherence_score, context_length, degradation_risk
                FROM context_tracking 
                WHERE session_id = ? AND timestamp > ?
                ORDER BY timestamp
            """, (session_id, since))
            
            context_data = cursor.fetchall()
            
            # 성능 트렌드
            cursor.execute("""
                SELECT timestamp, response_time_ms, tokens_processed, api_calls_count, error_count
                FROM performance_metrics 
                WHERE session_id = ? AND timestamp > ?
                ORDER BY timestamp
            """, (session_id, since))
            
            performance_data = cursor.fetchall()
            
            conn.close()
            
            return {
                'session_id': session_id,
                'memory_trend': memory_data,
                'context_trend': context_data,
                'performance_trend': performance_data,
                'analysis_period_hours': hours
            }
            
        except Exception as e:
            self.log(f"세션 분석 데이터 조회 실패: {e}", "ERROR")
            return {}
    
    def get_system_health(self) -> Dict:
        """시스템 헬스 상태 조회"""
        try:
            # 현재 시스템 상태
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.root))
            
            # 활성 세션 수
            active_sessions = len(self.get_active_sessions())
            
            # 최근 24시간 오류 수
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since_24h = datetime.now() - timedelta(hours=24)
            cursor.execute("""
                SELECT COUNT(*) FROM performance_metrics 
                WHERE timestamp > ? AND error_count > 0
            """, (since_24h,))
            
            error_count_24h = cursor.fetchone()[0]
            conn.close()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_free_gb': disk.free / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100
                },
                'gpt5': {
                    'active_sessions': active_sessions,
                    'errors_24h': error_count_24h,
                    'monitoring_status': 'active' if self.monitoring else 'inactive'
                }
            }
            
        except Exception as e:
            self.log(f"시스템 헬스 조회 실패: {e}", "ERROR")
            return {}
    
    def log_report_transmission(self, report_data: Dict) -> bool:
        """보고서 전송 로그 기록"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO report_transmissions 
                (report_id, report_type, recipient, transmission_method, status, file_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                report_data.get('report_id'),
                report_data.get('report_type'),
                report_data.get('recipient'),
                report_data.get('method'),
                report_data.get('status', 'sent'),
                report_data.get('file_path'),
                json.dumps(report_data.get('metadata', {}), ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
            self.log(f"보고서 전송 로그 기록: {report_data.get('report_id')}")
            return True
            
        except Exception as e:
            self.log(f"보고서 전송 로그 실패: {e}", "ERROR")
            return False
    
    def record_message(self, session_id: str, message_type: str, content: str, 
                      tokens: int = 0, context_used: Dict = None) -> bool:
        """대화 메시지 기록"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 한국시간으로 타임스탬프 생성
            korean_time = get_korean_timestamp()
            
            cursor.execute("""
                INSERT INTO conversation_messages 
                (session_id, timestamp, message_type, content, tokens, context_used)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                korean_time,
                message_type,
                content,
                tokens,
                json.dumps(context_used or {}, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
            self.log(f"메시지 기록: {session_id} ({message_type})")
            return True
            
        except Exception as e:
            self.log(f"메시지 기록 실패: {e}", "ERROR")
            return False
    
    def generate_session_summary(self, session_id: str, summary_type: str = "realtime") -> Dict:
        """세션 대화 요약 생성"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 최근 메시지들 조회 (실시간: 최근 10개, 세션 종료: 전체)
            limit_clause = "LIMIT 10" if summary_type == "realtime" else ""
            
            cursor.execute(f"""
                SELECT message_type, content, tokens, timestamp
                FROM conversation_messages 
                WHERE session_id = ?
                ORDER BY timestamp DESC {limit_clause}
            """, (session_id,))
            
            messages = cursor.fetchall()
            
            if not messages:
                return {"error": "메시지가 없습니다"}
            
            # 메시지 분석
            user_messages = [msg for msg in messages if msg[0] == 'user']
            assistant_messages = [msg for msg in messages if msg[0] == 'assistant']
            total_tokens = sum(msg[2] for msg in messages)
            
            # 주요 키워드 추출 (간단한 빈도 기반)
            keywords = self._extract_keywords(messages)
            
            # 대화 패턴 분석
            interaction_pattern = self._analyze_interaction_pattern(messages)
            
            # 내용 요약 생성
            content_summary = self._generate_content_summary(messages, summary_type)
            
            # 품질 메트릭 계산
            quality_metrics = {
                "response_consistency": self._calculate_consistency(messages),
                "topic_coherence": self._calculate_coherence(messages),
                "engagement_level": len(messages) / max(1, len(set(msg[0] for msg in messages)))
            }
            
            summary_data = {
                'session_id': session_id,
                'summary_type': summary_type,
                'topic_keywords': json.dumps(keywords, ensure_ascii=False),
                'content_summary': content_summary,
                'interaction_pattern': interaction_pattern,
                'quality_metrics': json.dumps(quality_metrics, ensure_ascii=False),
                'message_stats': {
                    'total_messages': len(messages),
                    'user_messages': len(user_messages),
                    'assistant_messages': len(assistant_messages),
                    'total_tokens': total_tokens
                }
            }
            
            # 요약 데이터베이스에 저장
            cursor.execute("""
                INSERT INTO session_summaries 
                (session_id, summary_type, topic_keywords, content_summary, 
                 interaction_pattern, quality_metrics)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                summary_type,
                summary_data['topic_keywords'],
                summary_data['content_summary'],
                summary_data['interaction_pattern'],
                summary_data['quality_metrics']
            ))
            
            conn.commit()
            conn.close()
            
            return summary_data
            
        except Exception as e:
            self.log(f"세션 요약 생성 실패: {e}", "ERROR")
            return {}
    
    def _extract_keywords(self, messages: List) -> List[str]:
        """메시지에서 주요 키워드 추출"""
        # 간단한 키워드 추출 (실제로는 NLP 라이브러리 사용 권장)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                       'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
                       'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                       '이', '가', '은', '는', '을', '를', '에', '에서', '로', '으로', '와', '과',
                       '그리고', '하지만', '그러나', '또한', '그래서', '따라서'}
        
        all_text = ' '.join(msg[1] for msg in messages if msg[1])
        words = all_text.lower().split()
        
        # 빈도 계산
        word_freq = {}
        for word in words:
            if len(word) > 2 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 상위 키워드 반환
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:10]
    
    def _analyze_interaction_pattern(self, messages: List) -> str:
        """상호작용 패턴 분석"""
        if len(messages) < 2:
            return "대화 시작 단계"
        
        user_msgs = len([m for m in messages if m[0] == 'user'])
        assistant_msgs = len([m for m in messages if m[0] == 'assistant'])
        
        if user_msgs > assistant_msgs * 1.5:
            return "사용자 주도적 대화"
        elif assistant_msgs > user_msgs * 1.5:
            return "AI 주도적 대화"
        else:
            return "균형있는 상호작용"
    
    def _generate_content_summary(self, messages: List, summary_type: str) -> str:
        """대화 내용 요약 생성"""
        if not messages:
            return "대화 내용이 없습니다."
        
        recent_topics = []
        for msg in messages[:5]:  # 최근 5개 메시지만 
            if msg[1] and len(msg[1]) > 10:  # 충분한 길이의 메시지만
                # 첫 50자만 요약으로 사용
                summary_text = msg[1][:50] + "..." if len(msg[1]) > 50 else msg[1]
                recent_topics.append(f"- {summary_text}")
        
        if summary_type == "realtime":
            return f"최근 대화 주제:\n" + "\n".join(recent_topics[:3])
        else:
            return f"주요 대화 내용:\n" + "\n".join(recent_topics)
    
    def _calculate_consistency(self, messages: List) -> float:
        """응답 일관성 점수 계산 (0-1)"""
        # 간단한 일관성 측정: 메시지 길이 편차 기반
        if len(messages) < 2:
            return 1.0
        
        lengths = [len(msg[1]) for msg in messages if msg[1]]
        if not lengths:
            return 1.0
            
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        # 정규화된 일관성 점수 (낮은 분산 = 높은 일관성)
        return max(0, 1 - (variance / (avg_length ** 2 + 1)))
    
    def _calculate_coherence(self, messages: List) -> float:
        """주제 일관성 점수 계산 (0-1)"""
        # 간단한 일관성 측정: 공통 키워드 비율
        if len(messages) < 2:
            return 1.0
        
        keywords_per_msg = [set(self._extract_keywords([msg])) for msg in messages if msg[1]]
        
        if len(keywords_per_msg) < 2:
            return 1.0
        
        # 메시지 간 공통 키워드 비율 계산
        common_keywords = set.intersection(*keywords_per_msg) if keywords_per_msg else set()
        all_keywords = set.union(*keywords_per_msg) if keywords_per_msg else set()
        
        return len(common_keywords) / len(all_keywords) if all_keywords else 1.0
    
    def get_recent_conversation_summaries(self, hours: int = 1) -> List[Dict]:
        """최근 대화 요약들 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT s.session_id, s.content_summary, s.topic_keywords, 
                       s.interaction_pattern, s.quality_metrics, s.timestamp,
                       g.message_count
                FROM session_summaries s
                JOIN gpt5_sessions g ON s.session_id = g.session_id
                WHERE s.timestamp > ? AND s.summary_type = 'realtime'
                ORDER BY s.timestamp DESC
            """, (since,))
            
            summaries = []
            for row in cursor.fetchall():
                summaries.append({
                    'session_id': row[0],
                    'content_summary': row[1],
                    'topic_keywords': json.loads(row[2]) if row[2] else [],
                    'interaction_pattern': row[3],
                    'quality_metrics': json.loads(row[4]) if row[4] else {},
                    'timestamp': row[5],
                    'message_count': row[6]
                })
            
            conn.close()
            return summaries
            
        except Exception as e:
            self.log(f"대화 요약 조회 실패: {e}", "ERROR")
            return []
    
    def migrate_existing_dialog_data(self) -> Dict:
        """기존 VELOS dialog_memory.json 데이터를 GPT-5 모니터링 시스템으로 마이그레이션"""
        try:
            dialog_memory_path = self.root / "data" / "memory" / "dialog_memory.json"
            
            if not dialog_memory_path.exists():
                return {"status": "error", "message": "dialog_memory.json 파일을 찾을 수 없습니다"}
            
            # 기존 데이터 로드
            with open(dialog_memory_path, 'r', encoding='utf-8') as f:
                dialog_data = json.load(f)
            
            migrated_sessions = 0
            migrated_messages = 0
            
            for session_data in dialog_data.get('sessions', []):
                session_id = session_data['session_id']
                created_at = session_data['created_at']
                conversations = session_data.get('conversations', [])
                
                # 세션 생성 (이미 존재하면 건너뛰기)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM gpt5_sessions WHERE session_id = ?", (session_id,))
                if cursor.fetchone()[0] == 0:
                    # 새 세션 생성
                    cursor.execute("""
                        INSERT INTO gpt5_sessions 
                        (session_id, start_time, message_count, status) 
                        VALUES (?, ?, ?, 'completed')
                    """, (session_id, created_at, len(conversations)))
                    migrated_sessions += 1
                
                # 대화 메시지 마이그레이션
                for conv in conversations:
                    role = conv['role']
                    message = conv['message']
                    timestamp = conv['timestamp']
                    
                    # 메시지가 이미 존재하는지 확인
                    cursor.execute("""
                        SELECT COUNT(*) FROM conversation_messages 
                        WHERE session_id = ? AND timestamp = ? AND message_type = ?
                    """, (session_id, timestamp, role))
                    
                    if cursor.fetchone()[0] == 0:
                        # 토큰 수 추정 (단어 수 * 1.3)
                        estimated_tokens = int(len(message.split()) * 1.3) if message else 0
                        
                        cursor.execute("""
                            INSERT INTO conversation_messages 
                            (session_id, timestamp, message_type, content, tokens, context_used)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (session_id, timestamp, role, message, estimated_tokens, '{}'))
                        migrated_messages += 1
                
                # 세션 요약 생성 (기존 대화 기반)
                if conversations:
                    summary_data = self.generate_session_summary(session_id, 'migration')
                    if summary_data and 'error' not in summary_data:
                        self.log(f"세션 {session_id} 요약 생성 완료")
                
                conn.commit()
                conn.close()
            
            result = {
                "status": "success",
                "migrated_sessions": migrated_sessions,
                "migrated_messages": migrated_messages,
                "total_sessions": len(dialog_data.get('sessions', [])),
                "message": f"{migrated_sessions}개 세션, {migrated_messages}개 메시지 마이그레이션 완료"
            }
            
            self.log(f"데이터 마이그레이션 완료: {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"데이터 마이그레이션 실패: {e}"
            self.log(error_msg, "ERROR")
            return {"status": "error", "message": error_msg}


# 전역 모니터 인스턴스
_gpt5_monitor = None

def get_gpt5_monitor() -> GPT5Monitor:
    """GPT-5 모니터 싱글톤 인스턴스 반환"""
    global _gpt5_monitor
    if _gpt5_monitor is None:
        _gpt5_monitor = GPT5Monitor()
    return _gpt5_monitor