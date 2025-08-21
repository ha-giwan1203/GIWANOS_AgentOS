#!/usr/bin/env python3
# =========================================================
# VELOS 메모리 분석 인텔리전스 보고서 생성기
# 학습 패턴, 지식 증가, 메모리 효율성 심층 분석
# =========================================================

import json
import time
import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
import hashlib

# Use correct path for sandbox environment
ROOT = Path("/home/user/webapp")

class MemoryIntelligenceAnalyzer:
    """메모리 인텔리전스 분석기"""
    
    def __init__(self, analysis_depth: str = "deep"):
        self.root = ROOT
        self.memory_dir = self.root / "data" / "memory"
        self.logs_dir = self.root / "data" / "logs"
        self.analysis_depth = analysis_depth  # shallow, standard, deep
        
        # 키워드 분류
        self.technical_keywords = {
            "development": ["python", "javascript", "code", "function", "api", "debug", "error", "fix"],
            "system": ["memory", "database", "file", "path", "config", "environment", "server"],
            "ai_ml": ["gpt", "ai", "model", "learning", "training", "neural", "intelligence"],  
            "integration": ["slack", "notion", "webhook", "integration", "bridge", "dispatch"],
            "operations": ["backup", "log", "monitor", "health", "performance", "optimization"]
        }
    
    def load_json_safe(self, file_path: Path) -> Dict[str, Any]:
        """안전한 JSON 로딩"""
        if not file_path.exists():
            return {}
        try:
            content = file_path.read_text(encoding="utf-8")
            # BOM 제거
            if content.startswith('\ufeff'):
                content = content[1:]
            return json.loads(content)
        except Exception as e:
            print(f"[WARN] JSON 로딩 실패 {file_path}: {e}")
            return {}
    
    def analyze_memory_database(self) -> Dict[str, Any]:
        """메모리 데이터베이스 심층 분석"""
        db_analysis = {
            "total_records": 0,
            "record_types": {},
            "growth_pattern": {},
            "content_analysis": {},
            "quality_metrics": {},
            "insights": []
        }
        
        # DB 파일 찾기
        db_files = list(self.root.glob("**/*.db"))
        if not db_files:
            db_analysis["insights"].append("⚠️ SQLite DB 파일을 찾을 수 없음")
            return db_analysis
            
        try:
            # 가장 최근 DB 파일 사용
            latest_db = max(db_files, key=lambda x: x.stat().st_mtime)
            
            with sqlite3.connect(latest_db) as conn:
                cursor = conn.cursor()
                
                # 테이블 정보 수집
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table_name, in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        db_analysis["record_types"][table_name] = count
                        db_analysis["total_records"] += count
                        
                        # 메인 메모리 테이블 분석
                        if "memory" in table_name.lower() or "learning" in table_name.lower():
                            self._analyze_memory_table(cursor, table_name, db_analysis)
                            
                    except sqlite3.Error as e:
                        print(f"[WARN] 테이블 {table_name} 분석 실패: {e}")
                        
        except Exception as e:
            db_analysis["insights"].append(f"⚠️ DB 분석 중 오류: {str(e)}")
        
        return db_analysis
    
    def _analyze_memory_table(self, cursor: sqlite3.Cursor, table_name: str, analysis: Dict[str, Any]):
        """메모리 테이블 상세 분석"""
        try:
            # 컬럼 정보 확인
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 최근 레코드 샘플링
            limit = 100 if self.analysis_depth == "deep" else 20
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT {limit}")
            recent_records = cursor.fetchall()
            
            if recent_records:
                analysis["content_analysis"][table_name] = {
                    "columns": columns,
                    "recent_sample_size": len(recent_records),
                    "content_patterns": self._extract_content_patterns(recent_records, columns)
                }
                
        except sqlite3.Error as e:
            print(f"[WARN] 메모리 테이블 {table_name} 분석 실패: {e}")
    
    def _extract_content_patterns(self, records: List[Tuple], columns: List[str]) -> Dict[str, Any]:
        """레코드에서 콘텐츠 패턴 추출"""
        patterns = {
            "topic_distribution": Counter(),
            "content_types": Counter(),
            "language_patterns": Counter(),
            "complexity_levels": {"simple": 0, "medium": 0, "complex": 0}
        }
        
        # 텍스트 컬럼 찾기
        text_columns = []
        for i, col in enumerate(columns):
            if any(keyword in col.lower() for keyword in ["content", "text", "raw", "insight", "summary"]):
                text_columns.append(i)
        
        for record in records:
            for col_idx in text_columns:
                if col_idx < len(record) and record[col_idx]:
                    content = str(record[col_idx]).lower()
                    
                    # 주제 분류
                    for category, keywords in self.technical_keywords.items():
                        for keyword in keywords:
                            if keyword in content:
                                patterns["topic_distribution"][category] += 1
                    
                    # 언어 패턴
                    if re.search(r'[가-힣]', content):
                        patterns["language_patterns"]["korean"] += 1
                    if re.search(r'[a-zA-Z]', content):
                        patterns["language_patterns"]["english"] += 1
                    
                    # 복잡도 분석
                    word_count = len(content.split())
                    if word_count < 10:
                        patterns["complexity_levels"]["simple"] += 1
                    elif word_count < 50:
                        patterns["complexity_levels"]["medium"] += 1
                    else:
                        patterns["complexity_levels"]["complex"] += 1
        
        return patterns
    
    def analyze_jsonl_memory(self) -> Dict[str, Any]:
        """JSONL 메모리 파일 분석"""
        jsonl_analysis = {
            "files_analyzed": 0,
            "total_entries": 0,
            "temporal_patterns": {},
            "content_insights": {},
            "learning_velocity": "unknown"
        }
        
        jsonl_files = list(self.memory_dir.glob("*.jsonl"))
        
        for jsonl_file in jsonl_files:
            jsonl_analysis["files_analyzed"] += 1
            
            try:
                content = jsonl_file.read_text(encoding="utf-8")
                if content.startswith('\ufeff'):
                    content = content[1:]
                    
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                jsonl_analysis["total_entries"] += len(lines)
                
                # 시간별 패턴 분석
                timestamps = []
                topics = Counter()
                
                for line in lines:
                    try:
                        entry = json.loads(line)
                        
                        # 타임스탬프 분석
                        if "ts" in entry:
                            timestamps.append(entry["ts"])
                        elif "timestamp" in entry:
                            if entry["timestamp"] != "now":
                                try:
                                    ts = datetime.fromisoformat(entry["timestamp"]).timestamp()
                                    timestamps.append(ts)
                                except:
                                    pass
                        
                        # 주제 분석
                        raw_content = entry.get("raw", entry.get("summary", "")).lower()
                        for category, keywords in self.technical_keywords.items():
                            for keyword in keywords:
                                if keyword in raw_content:
                                    topics[category] += 1
                                    
                    except json.JSONDecodeError:
                        continue
                
                # 시간 패턴 분석
                if timestamps:
                    timestamps.sort()
                    if len(timestamps) > 1:
                        time_diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                        avg_interval = sum(time_diffs) / len(time_diffs) / 3600  # 시간 단위
                        
                        if avg_interval < 1:
                            jsonl_analysis["learning_velocity"] = "매우 빠름 (시간당 다수)"
                        elif avg_interval < 24:
                            jsonl_analysis["learning_velocity"] = "빠름 (일일 다수)"
                        elif avg_interval < 168:
                            jsonl_analysis["learning_velocity"] = "보통 (주간 다수)"
                        else:
                            jsonl_analysis["learning_velocity"] = "느림 (월간 소수)"
                
                jsonl_analysis["content_insights"]["topic_distribution"] = dict(topics.most_common(10))
                
            except Exception as e:
                print(f"[WARN] JSONL 파일 {jsonl_file.name} 분석 실패: {e}")
        
        return jsonl_analysis
    
    def analyze_learning_patterns(self) -> Dict[str, Any]:
        """학습 패턴 분석"""
        learning_analysis = {
            "learning_style": "unknown",
            "knowledge_domains": {},
            "retention_patterns": {},
            "learning_efficiency": "unknown",
            "recommendations": []
        }
        
        # 시스템 건강 데이터에서 학습 지표 추출
        health_data = self.load_json_safe(self.logs_dir / "system_health.json")
        
        if health_data:
            # 세션 부트스트랩 데이터
            bootstrap_count = health_data.get("session_bootstrap_count", 0)
            flush_moved = health_data.get("session_bootstrap_flush_moved", 0)
            
            if bootstrap_count > 0 and flush_moved > 0:
                efficiency_ratio = flush_moved / bootstrap_count
                if efficiency_ratio > 5:
                    learning_analysis["learning_efficiency"] = "높음"
                    learning_analysis["recommendations"].append("✅ 높은 학습 효율성 - 현재 패턴 유지")
                elif efficiency_ratio > 2:
                    learning_analysis["learning_efficiency"] = "보통"
                else:
                    learning_analysis["learning_efficiency"] = "낮음"
                    learning_analysis["recommendations"].append("💡 학습 효율성 개선 필요 - 더 체계적인 정보 수집")
            
            # 메모리 파이프라인 성능
            pipeline_ok = health_data.get("memory_pipeline_last_test_ok", False)
            if pipeline_ok:
                learning_analysis["retention_patterns"]["pipeline_health"] = "정상"
            else:
                learning_analysis["retention_patterns"]["pipeline_health"] = "이슈"
                learning_analysis["recommendations"].append("⚠️ 메모리 파이프라인 점검 필요")
        
        return learning_analysis
    
    def generate_memory_insights(self, db_analysis: Dict, jsonl_analysis: Dict, learning_analysis: Dict) -> List[str]:
        """메모리 인사이트 생성"""
        insights = []
        
        # 데이터 볼륨 인사이트
        total_records = db_analysis.get("total_records", 0) + jsonl_analysis.get("total_entries", 0)
        if total_records > 1000:
            insights.append(f"🎓 풍부한 학습 데이터: 총 {total_records:,}개 레코드 보유")
        elif total_records > 100:
            insights.append(f"📚 적정 학습 데이터: {total_records:,}개 레코드")
        else:
            insights.append(f"📖 초기 학습 단계: {total_records:,}개 레코드")
        
        # 학습 속도 인사이트
        velocity = jsonl_analysis.get("learning_velocity", "unknown")
        if velocity != "unknown":
            insights.append(f"⚡ 학습 속도: {velocity}")
        
        # 주제 다양성 인사이트
        topics = jsonl_analysis.get("content_insights", {}).get("topic_distribution", {})
        if topics:
            top_topic = max(topics.keys(), key=lambda x: topics[x])
            insights.append(f"🎯 주력 학습 분야: {top_topic} ({topics[top_topic]}건)")
            
            diversity_score = len(topics)
            if diversity_score >= 4:
                insights.append(f"🌈 다양한 학습 영역: {diversity_score}개 분야 활발")
            elif diversity_score >= 2:
                insights.append(f"📊 집중 학습: {diversity_score}개 주요 분야")
            else:
                insights.append("🎯 특화 학습: 단일 분야 집중")
        
        # 학습 효율성 인사이트
        efficiency = learning_analysis.get("learning_efficiency", "unknown")
        if efficiency != "unknown":
            insights.append(f"📈 학습 효율성: {efficiency}")
        
        return insights
    
    def generate_title(self, analysis_results: Dict[str, Any]) -> str:
        """분석 결과에 따른 동적 제목 생성"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 총 데이터량 기반 제목 결정
        total_records = (analysis_results.get("database", {}).get("total_records", 0) + 
                        analysis_results.get("jsonl", {}).get("total_entries", 0))
        
        learning_efficiency = analysis_results.get("learning", {}).get("learning_efficiency", "unknown")
        
        if total_records > 1500:
            if learning_efficiency == "높음":
                return f"🧠 VELOS 메모리 분석 - 고효율 학습 시스템 ({timestamp})"
            else:
                return f"📊 VELOS 메모리 분석 - 대용량 데이터 활용 ({timestamp})"
        elif total_records > 500:
            return f"🎓 VELOS 메모리 분석 - 안정적 학습 진행 ({timestamp})"
        else:
            return f"🌱 VELOS 메모리 분석 - 초기 학습 단계 ({timestamp})"
    
    def generate_intelligence_content(self) -> Dict[str, Any]:
        """전체 메모리 인텔리전스 콘텐츠 생성"""
        print("[INFO] 메모리 인텔리전스 심층 분석 중...")
        
        # 분석 실행
        db_analysis = self.analyze_memory_database()
        jsonl_analysis = self.analyze_jsonl_memory()
        learning_analysis = self.analyze_learning_patterns()
        
        analysis_results = {
            "database": db_analysis,
            "jsonl": jsonl_analysis,
            "learning": learning_analysis
        }
        
        # 제목 생성
        title = self.generate_title(analysis_results)
        
        # 인사이트 생성
        insights = self.generate_memory_insights(db_analysis, jsonl_analysis, learning_analysis)
        
        # 추천사항 수집
        all_recommendations = []
        all_recommendations.extend(learning_analysis.get("recommendations", []))
        
        return {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "analysis_depth": self.analysis_depth,
            "database": db_analysis,
            "jsonl": jsonl_analysis, 
            "learning": learning_analysis,
            "insights": insights,
            "recommendations": all_recommendations
        }

def generate_memory_intelligence_report(depth: str = "deep") -> str:
    """메모리 인텔리전스 보고서 생성"""
    analyzer = MemoryIntelligenceAnalyzer(depth)
    report_data = analyzer.generate_intelligence_content()
    
    # 마크다운 형식으로 보고서 생성
    report_lines = []
    
    # 제목
    report_lines.append(f"# {report_data['title']}")
    report_lines.append(f"**분석 깊이**: {report_data['analysis_depth'].upper()}")
    report_lines.append("")
    
    # 핵심 인사이트
    if report_data["insights"]:
        report_lines.append("## 💡 핵심 인사이트")
        for insight in report_data["insights"]:
            report_lines.append(f"- {insight}")
        report_lines.append("")
    
    # 데이터베이스 분석
    db_data = report_data["database"]
    report_lines.append("## 🗄️ 메모리 데이터베이스 분석")
    report_lines.append(f"- **총 레코드**: {db_data['total_records']:,}개")
    
    if db_data["record_types"]:
        report_lines.append("- **테이블별 분포**:")
        for table, count in db_data["record_types"].items():
            report_lines.append(f"  - {table}: {count:,}개")
    
    if db_data["content_analysis"]:
        report_lines.append("- **콘텐츠 분석**:")
        for table, analysis in db_data["content_analysis"].items():
            patterns = analysis.get("content_patterns", {})
            if patterns.get("topic_distribution"):
                top_topics = dict(Counter(patterns["topic_distribution"]).most_common(3))
                report_lines.append(f"  - {table} 주요 주제: {', '.join(f'{k}({v})' for k, v in top_topics.items())}")
    
    for insight in db_data.get("insights", []):
        report_lines.append(f"- {insight}")
    report_lines.append("")
    
    # JSONL 분석
    jsonl_data = report_data["jsonl"]
    report_lines.append("## 📝 실시간 메모리 분석")
    report_lines.append(f"- **분석 파일**: {jsonl_data['files_analyzed']}개")
    report_lines.append(f"- **총 엔트리**: {jsonl_data['total_entries']:,}개")
    report_lines.append(f"- **학습 속도**: {jsonl_data['learning_velocity']}")
    
    topics = jsonl_data.get("content_insights", {}).get("topic_distribution", {})
    if topics:
        report_lines.append("- **주요 학습 주제**:")
        for topic, count in list(topics.items())[:5]:
            report_lines.append(f"  - {topic}: {count}건")
    report_lines.append("")
    
    # 학습 패턴 분석
    learning_data = report_data["learning"]
    report_lines.append("## 🎓 학습 패턴 분석")
    report_lines.append(f"- **학습 효율성**: {learning_data['learning_efficiency']}")
    
    retention = learning_data.get("retention_patterns", {})
    if retention:
        report_lines.append("- **기억 보존 상태**:")
        for pattern, status in retention.items():
            status_icon = "✅" if status == "정상" else "⚠️"
            report_lines.append(f"  - {pattern}: {status_icon} {status}")
    report_lines.append("")
    
    # 권고사항
    if report_data["recommendations"]:
        report_lines.append("## 🎯 개선 권고사항")
        for rec in report_data["recommendations"]:
            report_lines.append(f"- {rec}")
        report_lines.append("")
    
    # 생성 정보
    report_lines.append("---")
    report_lines.append(f"*생성시간: {report_data['timestamp']}*")
    report_lines.append("*VELOS 메모리 인텔리전스 보고서 v1.0*")
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    import sys
    depth = sys.argv[1] if len(sys.argv) > 1 else "deep"
    report_content = generate_memory_intelligence_report(depth)
    print(report_content)