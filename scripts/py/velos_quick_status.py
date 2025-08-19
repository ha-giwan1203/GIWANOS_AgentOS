# [ACTIVE] VELOS 시스템 빠른 상태 확인 스크립트
# 헷갈리지 않게 핵심 상태만 한눈에 확인
import os
import json
from pathlib import Path
from datetime import datetime


def load_env():
    """환경변수 로딩"""
    env_file = Path("configs/.env")
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            return True
        except Exception:
            return False
    return False


def check_velos_status():
    """VELOS 시스템 핵심 상태 확인"""
    print("🔍 VELOS 시스템 상태 확인")
    print("=" * 50)
    
    status = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall": "unknown",
        "components": {}
    }
    
    # 1. 데이터베이스 상태
    print("📊 데이터베이스:")
    db_path = Path("data/velos.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"  ✅ DB 존재: {size_mb:.1f}MB")
        status["components"]["database"] = "✅ 정상"
        
        # 스키마 버전 확인
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM memory_fts")
            fts_count = cursor.fetchone()[0]
            conn.close()
            print(f"  ✅ 스키마 v{version}, FTS {fts_count}행")
        except Exception as e:
            print(f"  ⚠️ DB 접근 오류: {e}")
            status["components"]["database"] = "⚠️ 부분 오류"
    else:
        print("  ❌ DB 없음")
        status["components"]["database"] = "❌ 오류"
    
    # 2. 환경변수 상태
    print("\n🔧 환경변수:")
    load_env()
    env_vars = {
        "NOTION_TOKEN": os.getenv("NOTION_TOKEN"),
        "NOTION_DATABASE_ID": os.getenv("NOTION_DATABASE_ID"),
        "EMAIL_ENABLED": os.getenv("EMAIL_ENABLED"),
        "PUSHBULLET_TOKEN": os.getenv("PUSHBULLET_TOKEN")
    }
    
    env_ok = 0
    for var, value in env_vars.items():
        if value:
            print(f"  ✅ {var}: 설정됨")
            env_ok += 1
        else:
            print(f"  ❌ {var}: 없음")
    
    if env_ok >= 3:
        status["components"]["environment"] = "✅ 정상"
    elif env_ok >= 2:
        status["components"]["environment"] = "⚠️ 부분"
    else:
        status["components"]["environment"] = "❌ 오류"
    
    # 3. 보고서 상태
    print("\n📄 보고서:")
    auto_dir = Path("data/reports/auto")
    if auto_dir.exists():
        pdf_files = list(auto_dir.glob("velos_auto_report_*_ko.pdf"))
        md_files = list(auto_dir.glob("velos_auto_report_*.md"))
        print(f"  ✅ PDF: {len(pdf_files)}개, MD: {len(md_files)}개")
        
        if pdf_files:
            latest = max(pdf_files, key=lambda x: x.stat().st_mtime)
            latest_time = datetime.fromtimestamp(latest.stat().st_mtime)
            print(f"  ✅ 최신: {latest.name} ({latest_time.strftime('%m-%d %H:%M')})")
            status["components"]["reports"] = "✅ 정상"
        else:
            print("  ⚠️ 보고서 없음")
            status["components"]["reports"] = "⚠️ 없음"
    else:
        print("  ❌ 디렉토리 없음")
        status["components"]["reports"] = "❌ 오류"
    
    # 4. 알림 시스템 상태
    print("\n🔔 알림 시스템:")
    try:
        import requests
        requests_ok = True
    except ImportError:
        requests_ok = False
        print("  ❌ requests 없음")
    
    if requests_ok:
        # 간단한 알림 테스트
        notion_token = os.getenv("NOTION_TOKEN")
        email_enabled = os.getenv("EMAIL_ENABLED")
        pushbullet_token = os.getenv("PUSHBULLET_TOKEN")
        
        channels = []
        if notion_token:
            channels.append("Notion")
        if email_enabled == "1":
            channels.append("Email")
        if pushbullet_token:
            channels.append("Pushbullet")
        
        if channels:
            print(f"  ✅ 활성 채널: {', '.join(channels)}")
            status["components"]["notifications"] = "✅ 정상"
        else:
            print("  ⚠️ 활성 채널 없음")
            status["components"]["notifications"] = "⚠️ 부분"
    
    # 5. 핵심 스크립트 상태
    print("\n⚙️ 핵심 스크립트:")
    scripts = [
        "scripts/dispatch_report.py",
        "scripts/auto_generate_runner.py",
        "scripts/py/velos_system_integration_check.py"
    ]
    
    script_ok = 0
    for script in scripts:
        if Path(script).exists():
            print(f"  ✅ {script}")
            script_ok += 1
        else:
            print(f"  ❌ {script}")
    
    if script_ok == len(scripts):
        status["components"]["scripts"] = "✅ 정상"
    elif script_ok >= 2:
        status["components"]["scripts"] = "⚠️ 부분"
    else:
        status["components"]["scripts"] = "❌ 오류"
    
    # 전체 상태 판정
    components = status["components"]
    ok_count = sum(1 for status in components.values() if "✅" in status)
    error_count = sum(1 for status in components.values() if "❌" in status)
    
    if error_count == 0:
        status["overall"] = "🎉 완벽함"
    elif error_count <= 1:
        status["overall"] = "✅ 양호함"
    else:
        status["overall"] = "⚠️ 개선 필요"
    
    # 결과 출력
    print("\n" + "=" * 50)
    print(f"🏆 전체 상태: {status['overall']}")
    print(f"📊 정상: {ok_count}개, 오류: {error_count}개")
    
    print("\n📋 컴포넌트별 상태:")
    for component, comp_status in components.items():
        print(f"  • {component}: {comp_status}")
    
    # 빠른 명령어 안내
    print("\n🚀 빠른 명령어:")
    print("  • 전체 테스트: python scripts/py/velos_pipeline_test.py")
    print("  • 시스템 점검: python scripts/py/velos_system_integration_check.py")
    print("  • 알림 테스트: python scripts/dispatch_report.py")
    print("  • 보고서 생성: python scripts/auto_generate_runner.py")
    
    return status


def main():
    """메인 함수"""
    status = check_velos_status()
    
    # 상태 저장
    report_dir = Path("data/reports/auto")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"quick_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"\n📄 상태 보고서: {report_file}")


if __name__ == "__main__":
    main()
