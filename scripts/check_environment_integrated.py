# [EXPERIMENT] VELOS 환경 통합 검증 - 시스템 환경 검사
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문
"판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

VELOS 통합 환경변수 체크 스크립트
- VELOS 시스템 환경변수 확인
- 전송 채널 환경변수 확인
- 환경변수 파일 상태 확인
- 가상환경 상태 확인
"""

import os
import sys
from pathlib import Path

# UTF-8 인코딩 강제 설정
try:
    from modules.utils.utf8_force import setup_utf8_environment
    setup_utf8_environment()
except ImportError:
    # utils 모듈을 찾을 수 없는 경우 직접 설정
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def check_velos_environment():
    """VELOS 시스템 환경변수 확인"""
    print("=== VELOS 시스템 환경변수 ===")
    print("=" * 40)

    velos_vars = [
        "VELOS_ROOT",
        "VELOS_DB",
        "VELOS_MEM_FAST",
        "VELOS_LOG_DIR",
        "VELOS_REPORT_DIR",
        "VELOS_SNAPSHOT_DIR",
        "VELOS_MEMORY_ONLY",
        "VELOS_LOG_PATH",
        "VELOS_BACKUP",
        "VELOS_LOG_LEVEL",
        "VELOS_API_TIMEOUT",
        "VELOS_API_RETRIES",
        "VELOS_MAX_WORKERS",
        "VELOS_DEBUG"
    ]

    for var in velos_vars:
        value = os.environ.get(var, "NOT_SET")
        print(f"{var}={value}")

    print("\n=== VELOS 경로 검증 ===")
    print("=" * 25)

    # 기본값 확인
    root = os.environ.get("VELOS_ROOT", "/workspace")
    print(f"VELOS_ROOT exists: {os.path.exists(root)}")
    print(f"VELOS_ROOT is dir: {os.path.isdir(root)}")

    # 하위 디렉토리 확인
    subdirs = ["data", "scripts", "modules", "interface", "configs"]
    for subdir in subdirs:
        path = os.path.join(root, subdir)
        exists = os.path.exists(path)
        is_dir = os.path.isdir(path) if exists else False
        print(f"  {subdir}/: exists={exists}, is_dir={is_dir}")


def check_transport_environment():
    """전송 채널 환경변수 확인"""
    print("\n=== 전송 채널 환경변수 ===")
    print("=" * 35)

    transport_vars = {
        "Slack": [
            "SLACK_BOT_TOKEN",
            "SLACK_CHANNEL",
            "SLACK_DEFAULT_CHANNEL",
            "SLACK_CHANNEL_ID"
        ],
        "Notion": [
            "NOTION_TOKEN",
            "NOTION_DATABASE_ID",
            "NOTION_PARENT_PAGE"
        ],
        "Email": [
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USER",
            "SMTP_PASS",
            "EMAIL_TO",
            "EMAIL_FROM"
        ],
        "Pushbullet": [
            "PUSHBULLET_TOKEN"
        ],
        "Dispatch": [
            "DISPATCH_EMAIL",
            "DISPATCH_SLACK",
            "DISPATCH_NOTION",
            "DISPATCH_PUSH"
        ]
    }

    for channel, vars_list in transport_vars.items():
        print(f"\n{channel}:")
        for var in vars_list:
            value = os.getenv(var, "NOT_SET")
            # 민감한 정보는 마스킹
            if any(keyword in var.upper() for keyword in ['TOKEN', 'PASS', 'KEY']):
                if value != "NOT_SET":
                    print(f"  {var}: {'*' * min(len(value), 20)}...")
                else:
                    print(f"  {var}: {value}")
            else:
                print(f"  {var}: {value}")


def check_env_files():
    """환경변수 파일 상태 확인"""
    print("\n=== 환경변수 파일 상태 ===")
    print("=" * 30)

    env_files = [
        "configs/.env",
        "C:/Users/User/venvs/velos/.env",
        ".env"
    ]

    for env_file in env_files:
        file_path = Path(env_file)
        if file_path.exists():
            print(f"✅ {env_file} - 존재")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 전송 관련 환경변수만 필터링
                transport_vars = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if any(keyword in line for keyword in ['SLACK_', 'NOTION_', 'EMAIL_', 'PUSHBULLET_', 'DISPATCH_']):
                            transport_vars.append(line)
                
                print(f"  📊 총 {len(lines)}줄, 전송 관련 {len(transport_vars)}개")
                
                if transport_vars:
                    print("  📋 전송 관련 환경변수:")
                    for var in transport_vars[:5]:  # 처음 5개만 표시
                        if any(keyword in var.upper() for keyword in ['TOKEN', 'PASS', 'KEY']):
                            key, value = var.split('=', 1) if '=' in var else (var, '')
                            print(f"    {key}=***")
                        else:
                            print(f"    {var}")
                    
                    if len(transport_vars) > 5:
                        print(f"    ... 및 {len(transport_vars) - 5}개 더")
                        
            except Exception as e:
                print(f"  ❌ 파일 읽기 오류: {e}")
        else:
            print(f"❌ {env_file} - 없음")


def check_venv_health():
    """가상환경 상태 확인"""
    print("\n=== 가상환경 상태 ===")
    print("=" * 20)

    venv_paths = [
        "C:/Users/User/venvs/velos",
        "C:/giwanos/.venv",
        ".venv"
    ]

    for venv_path in venv_paths:
        path = Path(venv_path)
        if path.exists():
            print(f"✅ {venv_path} - 존재")
            
            # Python 실행 파일 확인
            python_exe = path / "Scripts" / "python.exe"
            if python_exe.exists():
                print(f"  🐍 Python: {python_exe}")
            else:
                print(f"  ❌ Python: 없음")
            
            # pip 확인
            pip_exe = path / "Scripts" / "pip.exe"
            if pip_exe.exists():
                print(f"  📦 pip: {pip_exe}")
            else:
                print(f"  ❌ pip: 없음")
                
        else:
            print(f"❌ {venv_path} - 없음")


def check_current_environment():
    """현재 환경 상태 요약"""
    print("\n=== 현재 환경 상태 요약 ===")
    print("=" * 35)

    # VELOS_ROOT 확인
    velos_root = os.getenv("VELOS_ROOT", "/workspace")
    root_exists = os.path.exists(velos_root)
    print(f"VELOS_ROOT: {'✅ 설정됨' if root_exists else '❌ 없음'} ({velos_root})")

    # 전송 채널 상태
    channels = {
        "Slack": bool(os.getenv("SLACK_BOT_TOKEN")),
        "Notion": bool(os.getenv("NOTION_TOKEN")),
        "Email": bool(os.getenv("SMTP_HOST")),
        "Pushbullet": bool(os.getenv("PUSHBULLET_TOKEN"))
    }

    print("\n전송 채널 상태:")
    for channel, enabled in channels.items():
        status = "✅ 활성화" if enabled else "❌ 비활성화"
        print(f"  {channel}: {status}")

    # 디스패치 설정
    dispatch_enabled = sum(1 for var in ["DISPATCH_EMAIL", "DISPATCH_SLACK", "DISPATCH_NOTION", "DISPATCH_PUSH"] 
                          if os.getenv(var) == "1")
    print(f"\n디스패치 활성화: {dispatch_enabled}/4 채널")


def main():
    """메인 실행 함수"""
    print("🔍 VELOS 통합 환경변수 체크")
    print("=" * 50)

    try:
        check_velos_environment()
        check_transport_environment()
        check_env_files()
        check_venv_health()
        check_current_environment()

        print("\n✅ 환경변수 체크 완료!")

    except Exception as e:
        print(f"\n❌ 환경변수 체크 중 오류 발생: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

