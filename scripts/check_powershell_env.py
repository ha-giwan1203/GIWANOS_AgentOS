# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

import subprocess
import sys
import os


def run_powershell_command(command):
    """PowerShell 명령을 실행하고 결과를 반환"""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
             '-Command', command],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return f"Error: {e}", ""


def main():
    print("=== PowerShell 환경 정보 확인 ===")
    print("=" * 50)

    # PowerShell 버전 확인
    stdout, stderr = run_powershell_command("$PSVersionTable.PSVersion.ToString()")
    print(f"PowerShell Version: {stdout}")

    # 호스트 이름 확인
    stdout, stderr = run_powershell_command("$Host.Name")
    print(f"Host Name: {stdout}")

    # 프로파일 경로 확인
    stdout, stderr = run_powershell_command("$PROFILE")
    print(f"Profile Path: {stdout}")

    # 인코딩 정보 확인
    encoding_cmd = '''
    $Enc = "[Default:{0}] [ConsoleOut:{1}] [ConsoleIn:{2}] [VarOut:{3}]" -f `
        [System.Text.Encoding]::Default.WebName,
        [Console]::OutputEncoding.WebName,
        [Console]::InputEncoding.WebName,
        $OutputEncoding.WebName
    $Enc
    '''
    stdout, stderr = run_powershell_command(encoding_cmd)
    print(f"Encoding Info: {stdout}")

    # 코드 페이지 확인
    stdout, stderr = run_powershell_command("chcp")
    print(f"Code Page: {stdout}")

    # 프로파일 존재 여부 확인
    stdout, stderr = run_powershell_command("Test-Path $PROFILE")
    profile_exists = "True" in stdout
    print(f"Profile Exists: {profile_exists}")

    if profile_exists:
        # 프로파일 내용 확인 (마지막 5줄)
        cmd = "Get-Content $PROFILE | Select-Object -Last 5"
        stdout, stderr = run_powershell_command(cmd)
        print("\nProfile Content (Last 5 lines):")
        print("-" * 30)
        print(stdout)

    print("\n=== Python 환경 정보 ===")
    print("=" * 30)
    print(f"Python Version: {sys.version}")
    print(f"Default Encoding: {sys.getdefaultencoding()}")
    print(f"File System Encoding: {sys.getfilesystemencoding()}")
    print(f"PYTHONUTF8: {os.environ.get('PYTHONUTF8', 'Not Set')}")
    print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'Not Set')}")

    print("\n[DONE] PowerShell 환경 정보 확인 완료!")


if __name__ == "__main__":
    main()
