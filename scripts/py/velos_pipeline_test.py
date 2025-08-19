# [ACTIVE] VELOS 시스템 전체 파이프라인 확인 및 가동 테스트
# 데이터베이스 → 보고서 생성 → 알림 전송 → Notion 동기화 → 모니터링
import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_env():
    """환경변수 로딩"""
    env_file = Path("configs/.env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            return True
        except Exception as e:
            print(f"❌ 환경변수 로딩 실패: {e}")
            return False
    else:
        print(f"❌ 환경변수 파일 없음: {env_file}")
        return False


class VELOSPipelineTester:
    """VELOS 시스템 전체 파이프라인 테스터"""
    
    def __init__(self):
        self.root = Path("C:/giwanos")
        self.results = {}
        self.start_time = datetime.now()
    
    def test_database_pipeline(self) -> Dict[str, Any]:
        """1단계: 데이터베이스 파이프라인 테스트"""
        print("🔍 1단계: 데이터베이스 파이프라인 테스트")
        print("-" * 50)
        
        results = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        # 1.1 데이터베이스 존재 확인
        db_path = self.root / "data/velos.db"
        if db_path.exists():
            results["details"]["db_exists"] = True
            results["details"]["db_size"] = f"{db_path.stat().st_size / 1024 / 1024:.2f} MB"
        else:
            results["details"]["db_exists"] = False
            results["errors"].append("데이터베이스 파일 없음")
        
        # 1.2 스키마 버전 확인
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            results["details"]["schema_version"] = version
            conn.close()
        except Exception as e:
            results["errors"].append(f"스키마 버전 확인 실패: {e}")
        
        # 1.3 FTS 상태 확인
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory_fts")
            fts_count = cursor.fetchone()[0]
            results["details"]["fts_rows"] = fts_count
            conn.close()
        except Exception as e:
            results["errors"].append(f"FTS 상태 확인 실패: {e}")
        
        # 1.4 테이블 수 확인
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            results["details"]["table_count"] = len(tables)
            results["details"]["tables"] = [table[0] for table in tables]
            conn.close()
        except Exception as e:
            results["errors"].append(f"테이블 수 확인 실패: {e}")
        
        # 결과 판정
        if not results["errors"]:
            results["status"] = "✅ 정상"
        else:
            results["status"] = "❌ 오류"
        
        self.results["database"] = results
        return results
    
    def test_report_generation_pipeline(self) -> Dict[str, Any]:
        """2단계: 보고서 생성 파이프라인 테스트"""
        print("\n🔍 2단계: 보고서 생성 파이프라인 테스트")
        print("-" * 50)
        
        results = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        # 2.1 자동 보고서 디렉토리 확인
        auto_dir = self.root / "data/reports/auto"
        if auto_dir.exists():
            results["details"]["auto_dir_exists"] = True
            
            # 기존 보고서 수 확인
            pdf_files = list(auto_dir.glob("velos_auto_report_*_ko.pdf"))
            md_files = list(auto_dir.glob("velos_auto_report_*.md"))
            results["details"]["existing_pdfs"] = len(pdf_files)
            results["details"]["existing_mds"] = len(md_files)
            
            if pdf_files:
                latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
                results["details"]["latest_pdf"] = latest_pdf.name
                results["details"]["latest_pdf_time"] = datetime.fromtimestamp(
                    latest_pdf.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            results["details"]["auto_dir_exists"] = False
            results["errors"].append("자동 보고서 디렉토리 없음")
        
        # 2.2 보고서 생성 스크립트 확인
        report_scripts = [
            "scripts/auto_generate_runner.py",
            "scripts/velos_ai_insights_report.py",
            "scripts/publish_report.py"
        ]
        
        for script in report_scripts:
            script_path = self.root / script
            if script_path.exists():
                results["details"][f"{script}_exists"] = True
            else:
                results["details"][f"{script}_exists"] = False
                results["errors"].append(f"스크립트 없음: {script}")
        
        # 2.3 테스트 보고서 생성
        try:
            print("  📄 테스트 보고서 생성 중...")
            result = subprocess.run(
                ["python", "scripts/auto_generate_runner.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                results["details"]["test_generation"] = "✅ 성공"
                results["details"]["generation_output"] = result.stdout[:200] + "..."
            else:
                results["details"]["test_generation"] = "❌ 실패"
                results["errors"].append(f"보고서 생성 실패: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            results["details"]["test_generation"] = "⏰ 타임아웃"
            results["errors"].append("보고서 생성 타임아웃")
        except Exception as e:
            results["details"]["test_generation"] = "❌ 오류"
            results["errors"].append(f"보고서 생성 오류: {e}")
        
        # 결과 판정
        if not results["errors"]:
            results["status"] = "✅ 정상"
        else:
            results["status"] = "❌ 오류"
        
        self.results["report_generation"] = results
        return results
    
    def test_notification_pipeline(self) -> Dict[str, Any]:
        """3단계: 알림 전송 파이프라인 테스트"""
        print("\n🔍 3단계: 알림 전송 파이프라인 테스트")
        print("-" * 50)
        
        results = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        # 3.1 최신 보고서 찾기
        auto_dir = self.root / "data/reports/auto"
        pdf_files = list(auto_dir.glob("velos_auto_report_*_ko.pdf"))
        md_files = list(auto_dir.glob("velos_auto_report_*.md"))
        
        if not pdf_files:
            results["errors"].append("전송할 PDF 파일 없음")
            results["status"] = "❌ 오류"
            self.results["notification"] = results
            return results
        
        latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
        latest_md = max(md_files, key=lambda x: x.stat().st_mtime) if md_files else None
        
        results["details"]["test_pdf"] = latest_pdf.name
        results["details"]["test_md"] = latest_md.name if latest_md else "None"
        
        # 3.2 디스패치 테스트
        try:
            print("  📤 알림 전송 테스트 중...")
            result = subprocess.run(
                ["python", "scripts/dispatch_report.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # JSON 결과 파싱
                try:
                    dispatch_result = json.loads(result.stdout)
                    results["details"]["dispatch_result"] = dispatch_result
                    
                    # 각 채널별 결과 확인
                    channels = ["slack", "notion", "email", "push"]
                    success_count = 0
                    
                    for channel in channels:
                        if channel in dispatch_result:
                            channel_result = dispatch_result[channel]
                            if channel_result.get("ok", False):
                                results["details"][f"{channel}_status"] = "✅ 성공"
                                success_count += 1
                            else:
                                results["details"][f"{channel}_status"] = f"❌ 실패: {channel_result.get('detail', 'unknown')}"
                                if channel in ["slack", "notion"]:
                                    results["errors"].append(f"{channel} 전송 실패: {channel_result.get('detail', 'unknown')}")
                    
                    results["details"]["success_rate"] = f"{success_count}/{len(channels)}"
                    
                except json.JSONDecodeError:
                    results["errors"].append("디스패치 결과 파싱 실패")
                    
            else:
                results["errors"].append(f"디스패치 실행 실패: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            results["errors"].append("디스패치 타임아웃")
        except Exception as e:
            results["errors"].append(f"디스패치 오류: {e}")
        
        # 결과 판정
        if not results["errors"]:
            results["status"] = "✅ 정상"
        else:
            results["status"] = "⚠️ 부분 오류"
        
        self.results["notification"] = results
        return results
    
    def test_notion_integration_pipeline(self) -> Dict[str, Any]:
        """4단계: Notion 통합 파이프라인 테스트"""
        print("\n🔍 4단계: Notion 통합 파이프라인 테스트")
        print("-" * 50)
        
        results = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        # 4.1 Notion 설정 확인
        notion_token = os.getenv("NOTION_TOKEN")
        notion_db_id = os.getenv("NOTION_DATABASE_ID")
        
        if notion_token:
            results["details"]["token_exists"] = True
            results["details"]["token_prefix"] = notion_token[:10] + "..."
        else:
            results["details"]["token_exists"] = False
            results["errors"].append("Notion 토큰 없음")
        
        if notion_db_id:
            results["details"]["database_id_exists"] = True
        else:
            results["details"]["database_id_exists"] = False
            results["errors"].append("Notion 데이터베이스 ID 없음")
        
        # 4.2 필드 매핑 확인
        mapping_files = [
            "configs/notion_field_mapping_fixed.json",
            "configs/notion_field_mapping.json"
        ]
        
        for mapping_file in mapping_files:
            mapping_path = self.root / mapping_file
            if mapping_path.exists():
                results["details"][f"{mapping_file}_exists"] = True
                try:
                    mapping_data = json.loads(mapping_path.read_text(encoding="utf-8"))
                    results["details"][f"{mapping_file}_fields"] = len(mapping_data.get("fields", {}))
                except Exception as e:
                    results["errors"].append(f"매핑 파일 파싱 실패: {mapping_file}")
                break
        else:
            results["errors"].append("필드 매핑 파일 없음")
        
        # 4.3 Notion API 테스트
        try:
            print("  🔗 Notion API 연결 테스트 중...")
            result = subprocess.run(
                ["python", "scripts/py/velos_notion_enhanced_dispatch.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                results["details"]["api_test"] = "✅ 성공"
                results["details"]["api_output"] = result.stdout[:200] + "..."
            else:
                results["details"]["api_test"] = "❌ 실패"
                results["errors"].append(f"API 테스트 실패: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            results["details"]["api_test"] = "⏰ 타임아웃"
            results["errors"].append("API 테스트 타임아웃")
        except Exception as e:
            results["details"]["api_test"] = "❌ 오류"
            results["errors"].append(f"API 테스트 오류: {e}")
        
        # 결과 판정
        if not results["errors"]:
            results["status"] = "✅ 정상"
        else:
            results["status"] = "⚠️ 부분 오류"
        
        self.results["notion_integration"] = results
        return results
    
    def test_monitoring_pipeline(self) -> Dict[str, Any]:
        """5단계: 모니터링 파이프라인 테스트"""
        print("\n🔍 5단계: 모니터링 파이프라인 테스트")
        print("-" * 50)
        
        results = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        # 5.1 시스템 상태 점검
        try:
            print("  📊 시스템 상태 점검 중...")
            result = subprocess.run(
                ["python", "scripts/py/velos_system_integration_check.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                results["details"]["system_check"] = "✅ 성공"
                results["details"]["system_output"] = result.stdout[:300] + "..."
            else:
                results["details"]["system_check"] = "❌ 실패"
                results["errors"].append(f"시스템 점검 실패: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            results["details"]["system_check"] = "⏰ 타임아웃"
            results["errors"].append("시스템 점검 타임아웃")
        except Exception as e:
            results["details"]["system_check"] = "❌ 오류"
            results["errors"].append(f"시스템 점검 오류: {e}")
        
        # 5.2 로그 디렉토리 확인
        log_dirs = [
            "data/logs",
            "data/reports/_dispatch",
            "data/reports/auto"
        ]
        
        for log_dir in log_dirs:
            log_path = self.root / log_dir
            if log_path.exists():
                results["details"][f"{log_dir}_exists"] = True
                results["details"][f"{log_dir}_files"] = len(list(log_path.glob("*")))
            else:
                results["details"][f"{log_dir}_exists"] = False
                results["errors"].append(f"로그 디렉토리 없음: {log_dir}")
        
        # 5.3 자동화 스크립트 확인
        automation_scripts = [
            "scripts/autosave_runner.ps1",
            "tools/velos-run.ps1"
        ]
        
        for script in automation_scripts:
            script_path = self.root / script
            if script_path.exists():
                results["details"][f"{script}_exists"] = True
            else:
                results["details"][f"{script}_exists"] = False
                results["errors"].append(f"자동화 스크립트 없음: {script}")
        
        # 결과 판정
        if not results["errors"]:
            results["status"] = "✅ 정상"
        else:
            results["status"] = "⚠️ 부분 오류"
        
        self.results["monitoring"] = results
        return results
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """전체 파이프라인 요약 보고서 생성"""
        print("\n📊 전체 파이프라인 요약 보고서")
        print("=" * 60)
        
        summary = {
            "test_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "overall_status": "unknown",
            "pipeline_status": {},
            "total_errors": 0,
            "recommendations": []
        }
        
        # 각 파이프라인 상태 확인
        pipelines = [
            ("database", "데이터베이스"),
            ("report_generation", "보고서 생성"),
            ("notification", "알림 전송"),
            ("notion_integration", "Notion 통합"),
            ("monitoring", "모니터링")
        ]
        
        for pipeline_key, pipeline_name in pipelines:
            if pipeline_key in self.results:
                result = self.results[pipeline_key]
                summary["pipeline_status"][pipeline_name] = result["status"]
                
                if result["status"] == "❌ 오류":
                    summary["total_errors"] += 1
                    summary["recommendations"].append(f"{pipeline_name} 파이프라인 오류 수정 필요")
                elif result["status"] == "⚠️ 부분 오류":
                    summary["recommendations"].append(f"{pipeline_name} 파이프라인 부분 개선 필요")
        
        # 전체 상태 판정
        if summary["total_errors"] == 0:
            summary["overall_status"] = "🎉 완벽함"
        elif summary["total_errors"] <= 2:
            summary["overall_status"] = "✅ 양호함"
        else:
            summary["overall_status"] = "⚠️ 개선 필요"
        
        # 결과 출력
        print(f"테스트 시간: {summary['test_time']}")
        print(f"소요 시간: {summary['duration']:.1f}초")
        print(f"전체 상태: {summary['overall_status']}")
        print(f"총 오류 수: {summary['total_errors']}개")
        
        print("\n📋 파이프라인별 상태:")
        for pipeline_name, status in summary["pipeline_status"].items():
            print(f"  • {pipeline_name}: {status}")
        
        if summary["recommendations"]:
            print("\n💡 권장사항:")
            for rec in summary["recommendations"]:
                print(f"  • {rec}")
        
        # 보고서 저장
        report_dir = self.root / "data/reports/auto"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        print(f"\n📄 상세 보고서 저장: {report_file}")
        
        return summary
    
    def run_full_pipeline_test(self):
        """전체 파이프라인 테스트 실행"""
        print("🚀 VELOS 시스템 전체 파이프라인 테스트 시작")
        print("=" * 60)
        
        # 각 파이프라인 테스트 실행
        self.test_database_pipeline()
        self.test_report_generation_pipeline()
        self.test_notification_pipeline()
        self.test_notion_integration_pipeline()
        self.test_monitoring_pipeline()
        
        # 요약 보고서 생성
        summary = self.generate_summary_report()
        
        print("\n" + "=" * 60)
        print("🎉 VELOS 시스템 전체 파이프라인 테스트 완료!")
        
        return summary


def main():
    """메인 함수"""
    if not load_env():
        print("❌ 환경변수 로딩 실패")
        return
    
    tester = VELOSPipelineTester()
    summary = tester.run_full_pipeline_test()
    
    # 최종 상태 출력
    print(f"\n🏆 최종 결과: {summary['overall_status']}")
    
    if summary["overall_status"] == "🎉 완벽함":
        print("✅ VELOS 시스템이 완벽하게 작동하고 있습니다!")
    elif summary["overall_status"] == "✅ 양호함":
        print("✅ VELOS 시스템이 양호하게 작동하고 있습니다.")
        print("일부 개선사항이 있지만 전체적으로 안정적입니다.")
    else:
        print("⚠️ VELOS 시스템에 개선이 필요한 부분이 있습니다.")
        print("위의 권장사항을 참고하여 수정해주세요.")


if __name__ == "__main__":
    main()
