#!/usr/bin/env python3
# [ACTIVE] VELOS 운영 철학 선언문
# =========================================================
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=/workspace 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

"""
VELOS 리눅스 환경 설정 스크립트
- 환경변수 설정
- 디렉토리 생성
- 의존성 확인
- autosave_runner 시작
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """VELOS 리눅스 환경을 설정합니다."""
    print("🔧 VELOS 리눅스 환경 설정 시작...")
    
    # 1. 환경변수 설정
    workspace = Path("/workspace").resolve()
    os.environ["VELOS_ROOT"] = str(workspace)
    os.environ["PYTHONPATH"] = f"{workspace}:{os.environ.get('PYTHONPATH', '')}"
    
    # PowerShell PATH 추가 (설치되어 있는 경우)
    home_local_bin = Path.home() / ".local" / "bin"
    if (home_local_bin / "pwsh").exists():
        current_path = os.environ.get("PATH", "")
        if str(home_local_bin) not in current_path:
            os.environ["PATH"] = f"{home_local_bin}:{current_path}"
            print(f"✅ PATH에 PowerShell 경로 추가: {home_local_bin}")
    
    print(f"✅ VELOS_ROOT: {os.environ['VELOS_ROOT']}")
    print(f"✅ PYTHONPATH: {os.environ['PYTHONPATH']}")
    
    # 2. 기본 디렉토리 생성
    required_dirs = [
        workspace / "data",
        workspace / "data" / "logs",
        workspace / "data" / "memory", 
        workspace / "data" / "reports" / "auto",
        workspace / "data" / "reports" / "_dispatch",
        workspace / "data" / "snapshots",
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 디렉토리: {dir_path}")
    
    # 3. 기본 임포트 테스트
    try:
        from modules.report_paths import ROOT, P
        print(f"✅ 기본 모듈 임포트 성공: ROOT={ROOT}")
    except Exception as e:
        print(f"❌ 임포트 실패: {e}")
        return False
    
    # 4. autosave_runner 상태 확인
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if "autosave_runner.py" in result.stdout:
            print("✅ autosave_runner 실행 중")
        else:
            print("⚠️  autosave_runner 중지됨 - 재시작 필요")
    except Exception:
        print("⚠️  autosave_runner 상태 확인 불가")
    
    # 5. PowerShell 테스트
    try:
        result = subprocess.run(["pwsh", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PowerShell v{result.stdout.strip().split()[-1]} 사용 가능")
        else:
            print("⚠️  PowerShell 실행 실패")
    except FileNotFoundError:
        print("⚠️  PowerShell 없음 - .ps1 스크립트는 건너뛰어집니다")
    
    print("\n🎉 VELOS 리눅스 환경 설정 완료!")
    print("\n📝 사용법 (혼합 환경):")
    print("export VELOS_ROOT='/workspace'")
    print("export PYTHONPATH='/workspace:$PYTHONPATH'")
    print("export PATH='$HOME/.local/bin:$PATH'")
    print("python3 scripts/velos_master_scheduler.py --list")
    
    return True

if __name__ == "__main__":
    success = setup_environment()
    sys.exit(0 if success else 1)