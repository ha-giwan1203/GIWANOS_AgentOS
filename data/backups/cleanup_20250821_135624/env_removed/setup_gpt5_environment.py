#!/usr/bin/env python3
# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# =========================================================
"""
VELOS GPT-5 환경 설정 스크립트

GPT-5 시스템 사용을 위한 환경 설정 및 검증
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

def check_python_version() -> bool:
    """Python 버전 확인 (3.8+ 필요)"""
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 8:
        print(f"✅ Python 버전: {sys.version} (지원됨)")
        return True
    else:
        print(f"❌ Python 버전: {sys.version} (3.8+ 필요)")
        return False

def check_required_packages() -> Tuple[bool, List[str]]:
    """필수 패키지 설치 확인"""
    required_packages = [
        "openai",
        "asyncio",
        "pathlib", 
        "dataclasses",
        "typing",
        "json",
        "sqlite3"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "asyncio":
                import asyncio
            elif package == "pathlib":
                from pathlib import Path
            elif package == "dataclasses":
                from dataclasses import dataclass
            elif package == "typing":
                from typing import Dict
            elif package == "json":
                import json
            elif package == "sqlite3":
                import sqlite3
            elif package == "openai":
                import openai
                print(f"✅ {package}: {openai.__version__}")
            else:
                __import__(package)
                print(f"✅ {package}: 설치됨")
        except ImportError:
            print(f"❌ {package}: 설치되지 않음")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def install_missing_packages(packages: List[str]) -> bool:
    """누락된 패키지 설치"""
    if not packages:
        return True
    
    print(f"\n📦 누락된 패키지 설치 중: {', '.join(packages)}")
    
    try:
        # openai가 누락된 경우
        if "openai" in packages:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "openai>=1.0.0"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ OpenAI 라이브러리 설치 완료")
            else:
                print(f"❌ OpenAI 라이브러리 설치 실패: {result.stderr}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 패키지 설치 실패: {str(e)}")
        return False

def check_openai_api_key() -> Tuple[bool, str]:
    """OpenAI API 키 확인"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY 환경변수가 설정되지 않음")
        return False, "환경변수 미설정"
    
    if not api_key.startswith("sk-"):
        print("⚠️  OPENAI_API_KEY 형식이 올바르지 않음 (sk-로 시작해야 함)")
        return False, "잘못된 형식"
    
    if len(api_key) < 20:
        print("⚠️  OPENAI_API_KEY 길이가 너무 짧음")
        return False, "길이 부족"
    
    print("✅ OPENAI_API_KEY 형식 검증 통과")
    return True, "정상"

def test_openai_connection() -> bool:
    """OpenAI API 연결 테스트"""
    try:
        import openai
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ API 키가 없어 연결 테스트 불가")
            return False
        
        print("🔍 OpenAI API 연결 테스트 중...")
        
        client = OpenAI(api_key=api_key)
        
        # 간단한 모델 목록 요청으로 연결 테스트
        models = client.models.list()
        
        # GPT-5 모델 확인
        gpt5_available = False
        for model in models.data:
            if "gpt-5" in model.id.lower():
                gpt5_available = True
                print(f"✅ GPT-5 모델 발견: {model.id}")
                break
        
        if not gpt5_available:
            print("⚠️  GPT-5 모델이 목록에 없음 (베타 액세스 필요할 수 있음)")
            # GPT-4를 대체로 테스트
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Hello, this is a test."}],
                    max_tokens=5
                )
                print("✅ OpenAI API 연결 성공 (GPT-4로 테스트)")
                return True
            except Exception as e:
                print(f"❌ API 연결 실패: {str(e)}")
                return False
        else:
            # GPT-5로 직접 테스트
            try:
                response = client.chat.completions.create(
                    model="gpt-5",
                    messages=[{"role": "user", "content": "Hello, this is a test."}],
                    max_tokens=5
                )
                print("✅ GPT-5 API 연결 성공!")
                return True
            except Exception as e:
                print(f"❌ GPT-5 API 연결 실패: {str(e)}")
                return False
        
    except Exception as e:
        print(f"❌ OpenAI 연결 테스트 실패: {str(e)}")
        return False

def check_velos_modules() -> Tuple[bool, List[str]]:
    """VELOS 모듈 확인"""
    velos_modules = [
        "modules.core.gpt5_client",
        "modules.core.velos_gpt5_memory", 
        "modules.core.memory_adapter",
        "modules.core.velos_chat_memory"
    ]
    
    missing_modules = []
    
    # 현재 디렉토리를 sys.path에 추가
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    for module in velos_modules:
        try:
            __import__(module)
            print(f"✅ {module}: 사용 가능")
        except ImportError as e:
            print(f"⚠️  {module}: 불러오기 실패 - {str(e)}")
            missing_modules.append(module)
    
    return len(missing_modules) == 0, missing_modules

def create_env_template() -> str:
    """환경변수 템플릿 파일 생성"""
    template_path = Path(__file__).parent.parent / "configs" / "gpt5_env_template.txt"
    template_path.parent.mkdir(exist_ok=True)
    
    template_content = """# VELOS GPT-5 환경변수 설정
# 이 파일을 참조하여 환경변수를 설정하세요

# OpenAI API 키 (필수)
export OPENAI_API_KEY="sk-your-api-key-here"

# VELOS 설정 (옵션)
export VELOS_ROOT="C:/giwanos"
export VELOS_DB_PATH="C:/giwanos/data/memory/velos.db"

# Windows에서는:
# set OPENAI_API_KEY=sk-your-api-key-here
# set VELOS_ROOT=C:/giwanos
# set VELOS_DB_PATH=C:/giwanos/data/memory/velos.db

# PowerShell에서는:
# $env:OPENAI_API_KEY="sk-your-api-key-here"
# $env:VELOS_ROOT="C:/giwanos"  
# $env:VELOS_DB_PATH="C:/giwanos/data/memory/velos.db"
"""
    
    template_path.write_text(template_content, encoding="utf-8")
    return str(template_path)

def run_basic_functionality_test() -> bool:
    """기본 기능 테스트"""
    try:
        print("\n🧪 VELOS GPT-5 기본 기능 테스트...")
        
        # GPT-5 클라이언트 테스트
        from modules.core.gpt5_client import GPT5Client, GPT5Request
        
        print("✅ GPT5Client 임포트 성공")
        
        # 메모리 통합 관리자 테스트
        from modules.core.velos_gpt5_memory import VELOSGPTMemoryIntegrator
        
        print("✅ VELOSGPTMemoryIntegrator 임포트 성공")
        
        # 헬스체크 테스트
        if os.getenv("OPENAI_API_KEY"):
            try:
                client = GPT5Client()
                health = client.health_check()
                print(f"✅ GPT-5 클라이언트 헬스체크: {health['status']}")
            except Exception as e:
                print(f"⚠️  GPT-5 클라이언트 초기화 실패: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 기능 테스트 실패: {str(e)}")
        return False

def generate_setup_report() -> Dict[str, Any]:
    """설정 리포트 생성"""
    report = {
        "timestamp": json.dumps(str(os.popen('date').read().strip())),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "setup_results": {},
        "recommendations": []
    }
    
    # 각 검사 결과 기록
    checks = [
        ("python_version", check_python_version()),
        ("required_packages", check_required_packages()[0]),
        ("openai_api_key", check_openai_api_key()[0]),
        ("velos_modules", check_velos_modules()[0])
    ]
    
    for check_name, result in checks:
        report["setup_results"][check_name] = result
    
    # 권장사항 생성
    if not report["setup_results"]["openai_api_key"]:
        report["recommendations"].append("OPENAI_API_KEY 환경변수를 설정하세요")
    
    if not report["setup_results"]["required_packages"]:
        report["recommendations"].append("pip install openai 명령으로 필요한 패키지를 설치하세요")
    
    if not report["setup_results"]["velos_modules"]:
        report["recommendations"].append("VELOS 모듈 경로를 확인하고 누락된 모듈을 복구하세요")
    
    return report

def main():
    """메인 설정 함수"""
    print("🚀 VELOS GPT-5 환경 설정 시작\n")
    
    # 1. Python 버전 확인
    print("1️⃣ Python 버전 확인")
    python_ok = check_python_version()
    print()
    
    # 2. 필수 패키지 확인
    print("2️⃣ 필수 패키지 확인")
    packages_ok, missing = check_required_packages()
    
    if not packages_ok:
        print(f"\n📦 누락된 패키지 자동 설치 시도...")
        install_success = install_missing_packages(missing)
        if install_success:
            packages_ok, _ = check_required_packages()  # 재확인
    print()
    
    # 3. OpenAI API 키 확인
    print("3️⃣ OpenAI API 키 확인")
    api_key_ok, key_status = check_openai_api_key()
    
    if api_key_ok:
        print("4️⃣ OpenAI API 연결 테스트")
        connection_ok = test_openai_connection()
    else:
        connection_ok = False
        print("4️⃣ API 키가 없어 연결 테스트 건너뜀")
    print()
    
    # 5. VELOS 모듈 확인
    print("5️⃣ VELOS 모듈 확인")
    modules_ok, missing_modules = check_velos_modules()
    print()
    
    # 6. 기본 기능 테스트
    if packages_ok and modules_ok:
        print("6️⃣ 기본 기능 테스트")
        functionality_ok = run_basic_functionality_test()
        print()
    else:
        functionality_ok = False
        print("6️⃣ 모듈 부족으로 기본 기능 테스트 건너뜀\n")
    
    # 7. 환경변수 템플릿 생성
    print("7️⃣ 환경변수 템플릿 생성")
    template_path = create_env_template()
    print(f"✅ 환경변수 템플릿 생성: {template_path}")
    print()
    
    # 8. 최종 리포트
    print("=" * 50)
    print("📋 VELOS GPT-5 환경 설정 결과")
    print("=" * 50)
    
    status_checks = [
        ("Python 버전", python_ok),
        ("필수 패키지", packages_ok),
        ("OpenAI API 키", api_key_ok),
        ("API 연결", connection_ok),
        ("VELOS 모듈", modules_ok),
        ("기본 기능", functionality_ok)
    ]
    
    all_ok = True
    for check_name, status in status_checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}: {'정상' if status else '문제 있음'}")
        if not status:
            all_ok = False
    
    print()
    
    if all_ok:
        print("🎉 모든 설정이 완료되었습니다!")
        print("이제 다음 명령으로 VELOS GPT-5를 사용할 수 있습니다:")
        print("  python -c \"from modules.core.velos_gpt5_memory import chat_velos_gpt5; print(chat_velos_gpt5('안녕하세요!'))\"")
    else:
        print("⚠️  일부 설정에 문제가 있습니다.")
        print("다음 사항들을 확인해 주세요:")
        if not api_key_ok:
            print(f"  - 환경변수 템플릿 참조: {template_path}")
        if not packages_ok:
            print("  - 누락된 패키지 수동 설치: pip install openai")
        if not modules_ok:
            print("  - VELOS 모듈 파일 확인")
    
    # 설정 리포트 저장
    report = generate_setup_report()
    report_path = Path(__file__).parent.parent / "data" / "logs" / "gpt5_setup_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📄 상세 리포트 저장: {report_path}")

if __name__ == "__main__":
    main()