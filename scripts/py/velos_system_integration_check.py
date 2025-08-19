# [ACTIVE] VELOS 전체 시스템 연동 점검 스크립트
# 데이터베이스 + 알림 + 보고서 + Notion + 환경변수 종합 점검
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


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


class SystemIntegrationChecker:
    """시스템 연동 점검 클래스"""
    
    def __init__(self):
        self.root = Path("C:/giwanos")
        self.results = {
            "database": {},
            "notifications": {},
            "reports": {},
            "notion": {},
            "environment": {},
            "dependencies": {},
            "overall": {}
        }
    
    def check_database(self) -> Dict[str, Any]:
        """데이터베이스 상태 점검"""
        print("🔍 데이터베이스 상태 점검 중...")
        
        db_path = Path("data/velos.db")
        db_status = {
            "exists": db_path.exists(),
            "size": 0,
            "schema_version": None,
            "fts_status": "unknown",
            "tables": [],
            "errors": []
        }
        
        if db_path.exists():
            db_status["size"] = db_path.stat().st_size
            
            # 스키마 버전 확인
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 스키마 버전
                cursor.execute("PRAGMA user_version")
                db_status["schema_version"] = cursor.fetchone()[0]
                
                # 테이블 목록
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                db_status["tables"] = [row[0] for row in cursor.fetchall()]
                
                # FTS 상태 확인
                if "memory_fts" in db_status["tables"]:
                    cursor.execute("SELECT COUNT(*) FROM memory_fts")
                    fts_count = cursor.fetchone()[0]
                    db_status["fts_status"] = f"active ({fts_count} rows)"
                else:
                    db_status["fts_status"] = "not_found"
                
                conn.close()
                
            except Exception as e:
                db_status["errors"].append(f"DB 접근 오류: {e}")
        
        self.results["database"] = db_status
        return db_status
    
    def check_notifications(self) -> Dict[str, Any]:
        """알림 시스템 점검"""
        print("🔍 알림 시스템 점검 중...")
        
        notification_status = {
            "email": {"enabled": False, "test_result": None},
            "pushbullet": {"enabled": False, "test_result": None},
            "slack": {"enabled": False, "test_result": None},
            "notion": {"enabled": False, "test_result": None}
        }
        
        # 이메일 설정 확인
        smtp_host = os.getenv("SMTP_HOST")
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        email_enabled = os.getenv("EMAIL_ENABLED", "0") == "1"
        
        if smtp_host and smtp_user and smtp_pass and email_enabled:
            notification_status["email"]["enabled"] = True
            # 이메일 테스트
            try:
                result = subprocess.run([
                    sys.executable, "tools/notifications/send_email.py",
                    "--subject", "VELOS 시스템 점검",
                    "--body", "시스템 연동 점검 테스트",
                    "--to", "test@example.com"
                ], capture_output=True, text=True, timeout=30)
                notification_status["email"]["test_result"] = result.returncode == 0
            except Exception as e:
                notification_status["email"]["test_result"] = False
        
        # Pushbullet 설정 확인
        pushbullet_token = os.getenv("PUSHBULLET_API_TOKEN")
        if pushbullet_token:
            notification_status["pushbullet"]["enabled"] = True
            # Pushbullet 테스트
            try:
                result = subprocess.run([
                    sys.executable, "tools/notifications/send_pushbullet_notification.py",
                    "--title", "VELOS 시스템 점검",
                    "--body", "시스템 연동 점검 테스트"
                ], capture_output=True, text=True, timeout=30)
                notification_status["pushbullet"]["test_result"] = result.returncode == 0
            except Exception as e:
                notification_status["pushbullet"]["test_result"] = False
        
        # Slack 설정 확인
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_token or slack_webhook:
            notification_status["slack"]["enabled"] = True
            notification_status["slack"]["test_result"] = "skipped"  # 보류 상태
        
        # Notion 설정 확인
        notion_token = os.getenv("NOTION_TOKEN")
        notion_db = os.getenv("NOTION_DATABASE_ID")
        if notion_token and notion_db:
            notification_status["notion"]["enabled"] = True
            # Notion 연결 테스트
            try:
                import requests
                url = f"https://api.notion.com/v1/databases/{notion_db}"
                headers = {
                    "Authorization": f"Bearer {notion_token}",
                    "Notion-Version": "2022-06-28"
                }
                response = requests.get(url, headers=headers, timeout=10)
                notification_status["notion"]["test_result"] = response.status_code == 200
            except Exception as e:
                notification_status["notion"]["test_result"] = False
        
        self.results["notifications"] = notification_status
        return notification_status
    
    def check_reports(self) -> Dict[str, Any]:
        """보고서 시스템 점검"""
        print("🔍 보고서 시스템 점검 중...")
        
        reports_status = {
            "auto_dir": {"exists": False, "count": 0},
            "latest_reports": [],
            "generation_working": False,
            "dispatch_working": False
        }
        
        # 자동 보고서 디렉토리 확인
        auto_dir = Path("data/reports/auto")
        if auto_dir.exists():
            reports_status["auto_dir"]["exists"] = True
            pdf_files = list(auto_dir.glob("velos_auto_report_*_ko.pdf"))
            reports_status["auto_dir"]["count"] = len(pdf_files)
            
            # 최근 보고서 목록
            recent_files = sorted(pdf_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            reports_status["latest_reports"] = [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in recent_files
            ]
        
        # 보고서 생성 테스트
        try:
            result = subprocess.run([
                sys.executable, "scripts/auto_generate_runner.py"
            ], capture_output=True, text=True, timeout=60)
            reports_status["generation_working"] = result.returncode == 0
        except Exception as e:
            reports_status["generation_working"] = False
        
        # 디스패치 테스트
        try:
            result = subprocess.run([
                sys.executable, "scripts/dispatch_report.py"
            ], capture_output=True, text=True, timeout=60)
            reports_status["dispatch_working"] = result.returncode == 0
        except Exception as e:
            reports_status["dispatch_working"] = False
        
        self.results["reports"] = reports_status
        return reports_status
    
    def check_notion_integration(self) -> Dict[str, Any]:
        """Notion 연동 점검"""
        print("🔍 Notion 연동 점검 중...")
        
        notion_status = {
            "field_mapping": {"exists": False, "fields": 0},
            "api_connection": False,
            "database_access": False,
            "automation_working": False
        }
        
        # 필드 매핑 확인
        mapping_file = Path("configs/notion_field_mapping.json")
        if mapping_file.exists():
            try:
                mapping_data = json.loads(mapping_file.read_text(encoding="utf-8"))
                notion_status["field_mapping"]["exists"] = True
                notion_status["field_mapping"]["fields"] = len(mapping_data.get("fields", {}))
            except Exception:
                pass
        
        # API 연결 확인
        notion_token = os.getenv("NOTION_TOKEN")
        notion_db = os.getenv("NOTION_DATABASE_ID")
        
        if notion_token and notion_db:
            try:
                import requests
                url = f"https://api.notion.com/v1/databases/{notion_db}"
                headers = {
                    "Authorization": f"Bearer {notion_token}",
                    "Notion-Version": "2022-06-28"
                }
                response = requests.get(url, headers=headers, timeout=10)
                notion_status["api_connection"] = response.status_code == 200
                notion_status["database_access"] = response.status_code == 200
            except Exception:
                pass
        
        # 자동화 스크립트 테스트
        try:
            result = subprocess.run([
                sys.executable, "scripts/py/velos_notion_integration.py"
            ], capture_output=True, text=True, timeout=120)
            notion_status["automation_working"] = result.returncode == 0
        except Exception:
            notion_status["automation_working"] = False
        
        self.results["notion"] = notion_status
        return notion_status
    
    def check_environment(self) -> Dict[str, Any]:
        """환경 설정 점검"""
        print("🔍 환경 설정 점검 중...")
        
        env_status = {
            "env_file_exists": False,
            "required_vars": {},
            "optional_vars": {},
            "missing_critical": []
        }
        
        # 환경변수 파일 확인
        env_file = Path("configs/.env")
        env_status["env_file_exists"] = env_file.exists()
        
        # 필수 환경변수 확인
        required_vars = [
            "VELOS_ROOT", "VELOS_DB_PATH", "NOTION_TOKEN", 
            "NOTION_DATABASE_ID", "PUSHBULLET_API_TOKEN"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            env_status["required_vars"][var] = {
                "set": value is not None,
                "value": value[:10] + "..." if value and len(value) > 10 else value
            }
            if not value:
                env_status["missing_critical"].append(var)
        
        # 선택적 환경변수 확인
        optional_vars = [
            "SMTP_HOST", "SMTP_USER", "SMTP_PASS", "EMAIL_ENABLED",
            "SLACK_BOT_TOKEN", "SLACK_WEBHOOK_URL"
        ]
        
        for var in optional_vars:
            value = os.getenv(var)
            env_status["optional_vars"][var] = {
                "set": value is not None,
                "value": value[:10] + "..." if value and len(value) > 10 else value
            }
        
        self.results["environment"] = env_status
        return env_status
    
    def check_dependencies(self) -> Dict[str, Any]:
        """의존성 점검"""
        print("🔍 의존성 점검 중...")
        
        deps_status = {
            "python_packages": {},
            "system_tools": {},
            "file_permissions": {}
        }
        
        # Python 패키지 확인 (실제 import 테스트)
        required_packages = [
            ("requests", "requests"),
            ("pushbullet.py", "pushbullet"),
            ("python-dotenv", "dotenv"),
            ("sqlite3", "sqlite3")
        ]
        
        for package_name, import_name in required_packages:
            try:
                if import_name == "sqlite3":
                    import sqlite3
                    deps_status["python_packages"][package_name] = True
                elif import_name == "dotenv":
                    from dotenv import load_dotenv
                    deps_status["python_packages"][package_name] = True
                else:
                    __import__(import_name)
                    deps_status["python_packages"][package_name] = True
            except ImportError as e:
                print(f"    ⚠️ {package_name} import 실패: {e}")
                deps_status["python_packages"][package_name] = False
            except Exception as e:
                print(f"    ⚠️ {package_name} 로드 오류: {e}")
                deps_status["python_packages"][package_name] = False
        
        # 시스템 도구 확인
        system_tools = ["python", "pip"]
        for tool in system_tools:
            try:
                result = subprocess.run([tool, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                deps_status["system_tools"][tool] = result.returncode == 0
            except Exception:
                deps_status["system_tools"][tool] = False
        
        # 파일 권한 확인
        critical_paths = [
            "data/", "configs/", "scripts/", "modules/"
        ]
        
        for path in critical_paths:
            path_obj = Path(path)
            deps_status["file_permissions"][path] = {
                "exists": path_obj.exists(),
                "readable": path_obj.exists() and os.access(path_obj, os.R_OK),
                "writable": path_obj.exists() and os.access(path_obj, os.W_OK)
            }
        
        self.results["dependencies"] = deps_status
        return deps_status
    
    def generate_overall_status(self) -> Dict[str, Any]:
        """전체 상태 종합"""
        print("🔍 전체 상태 종합 중...")
        
        # 각 영역별 상태 평가
        db_ok = (self.results["database"]["exists"] and 
                self.results["database"]["schema_version"] is not None)
        
        notifications_ok = any([
            self.results["notifications"]["email"]["enabled"],
            self.results["notifications"]["pushbullet"]["enabled"],
            self.results["notifications"]["notion"]["enabled"]
        ])
        
        reports_ok = (self.results["reports"]["auto_dir"]["exists"] and 
                     self.results["reports"]["generation_working"])
        
        notion_ok = (self.results["notion"]["api_connection"] and 
                    self.results["notion"]["field_mapping"]["exists"])
        
        env_ok = (self.results["environment"]["env_file_exists"] and 
                 len(self.results["environment"]["missing_critical"]) == 0)
        
        deps_ok = all(self.results["dependencies"]["python_packages"].values())
        
        # 전체 상태 계산
        total_checks = 6
        passed_checks = sum([db_ok, notifications_ok, reports_ok, notion_ok, env_ok, deps_ok])
        overall_score = (passed_checks / total_checks) * 100
        
        overall_status = {
            "score": overall_score,
            "status": "healthy" if overall_score >= 80 else "warning" if overall_score >= 60 else "critical",
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "component_status": {
                "database": "ok" if db_ok else "error",
                "notifications": "ok" if notifications_ok else "error",
                "reports": "ok" if reports_ok else "error",
                "notion": "ok" if notion_ok else "error",
                "environment": "ok" if env_ok else "error",
                "dependencies": "ok" if deps_ok else "error"
            }
        }
        
        self.results["overall"] = overall_status
        return overall_status
    
    def save_report(self, filename: str = "system_integration_report.json"):
        """점검 보고서 저장"""
        report_dir = Path("data/reports/auto")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / filename
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "results": self.results
        }
        
        report_file.write_text(
            json.dumps(report_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        print(f"✅ 시스템 연동 점검 보고서 저장: {report_file}")
        return report_file


def main():
    """메인 함수"""
    print("🔍 VELOS 전체 시스템 연동 점검 시작")
    print("=" * 60)
    
    # 환경변수 로딩
    if not load_env():
        print("❌ 환경변수 로딩 실패")
        return
    
    # 점검기 초기화
    checker = SystemIntegrationChecker()
    
    # 각 영역별 점검
    print("\n1️⃣ 데이터베이스 점검")
    db_status = checker.check_database()
    print(f"  • DB 존재: {db_status['exists']}")
    print(f"  • 스키마 버전: {db_status['schema_version']}")
    print(f"  • FTS 상태: {db_status['fts_status']}")
    print(f"  • 테이블 수: {len(db_status['tables'])}")
    
    print("\n2️⃣ 알림 시스템 점검")
    notif_status = checker.check_notifications()
    for channel, status in notif_status.items():
        print(f"  • {channel}: {'✅' if status['enabled'] else '❌'} "
              f"({'테스트 성공' if status['test_result'] else '테스트 실패' if status['test_result'] is False else '테스트 생략'})")
    
    print("\n3️⃣ 보고서 시스템 점검")
    reports_status = checker.check_reports()
    print(f"  • 자동 디렉토리: {reports_status['auto_dir']['exists']}")
    print(f"  • 보고서 수: {reports_status['auto_dir']['count']}")
    print(f"  • 생성 테스트: {'✅' if reports_status['generation_working'] else '❌'}")
    print(f"  • 디스패치 테스트: {'✅' if reports_status['dispatch_working'] else '❌'}")
    
    print("\n4️⃣ Notion 연동 점검")
    notion_status = checker.check_notion_integration()
    print(f"  • 필드 매핑: {'✅' if notion_status['field_mapping']['exists'] else '❌'}")
    print(f"  • API 연결: {'✅' if notion_status['api_connection'] else '❌'}")
    print(f"  • 데이터베이스 접근: {'✅' if notion_status['database_access'] else '❌'}")
    print(f"  • 자동화: {'✅' if notion_status['automation_working'] else '❌'}")
    
    print("\n5️⃣ 환경 설정 점검")
    env_status = checker.check_environment()
    print(f"  • 환경변수 파일: {'✅' if env_status['env_file_exists'] else '❌'}")
    print(f"  • 필수 변수 누락: {len(env_status['missing_critical'])}개")
    if env_status['missing_critical']:
        print(f"    - 누락: {', '.join(env_status['missing_critical'])}")
    
    print("\n6️⃣ 의존성 점검")
    deps_status = checker.check_dependencies()
    for package, available in deps_status['python_packages'].items():
        print(f"  • {package}: {'✅' if available else '❌'}")
    
    # 전체 상태 종합
    print("\n📊 전체 상태 종합")
    overall_status = checker.generate_overall_status()
    
    print(f"  • 점검 통과: {overall_status['passed_checks']}/{overall_status['total_checks']}")
    print(f"  • 전체 점수: {overall_status['score']:.1f}%")
    print(f"  • 상태: {overall_status['status'].upper()}")
    
    # 컴포넌트별 상태
    print("\n🔧 컴포넌트별 상태:")
    for component, status in overall_status['component_status'].items():
        print(f"  • {component}: {'✅' if status == 'ok' else '❌'}")
    
    # 보고서 저장
    report_file = checker.save_report()
    
    print("\n" + "=" * 60)
    print("🎉 시스템 연동 점검 완료!")
    print(f"📄 보고서: {report_file}")
    
    # 권장사항
    if overall_status['score'] < 80:
        print("\n⚠️ 권장사항:")
        if not db_status['exists']:
            print("  • 데이터베이스 파일이 없습니다. 재생성이 필요합니다.")
        if len(env_status['missing_critical']) > 0:
            print("  • 필수 환경변수가 누락되었습니다. configs/.env 파일을 확인하세요.")
        if not all(deps_status['python_packages'].values()):
            print("  • 일부 Python 패키지가 설치되지 않았습니다. pip install로 설치하세요.")


if __name__ == "__main__":
    main()
