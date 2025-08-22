# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
import os
import sys
import json
import time
import argparse
from typing import Dict, Any

ROOT = os.getenv("VELOS_ROOT", "/workspace")
if ROOT not in sys.path:
    sys.path.append(ROOT)

def run_system_integrity_check() -> Dict[str, Any]:
    """시스템 무결성 체크 실행"""
    try:
        import subprocess
        result = subprocess.run([
            sys.executable,
            os.path.join(ROOT, "scripts", "system_integrity_check.py")
        ], capture_output=True, text=True, timeout=30)

        # JSON 파싱 시도 (마지막 JSON 블록만 추출)
        try:
            # stdout에서 마지막 JSON 블록 찾기
            lines = result.stdout.strip().split('\n')
            json_lines = []
            in_json = False

            for line in reversed(lines):
                if line.strip() == '}':
                    in_json = True
                if in_json:
                    json_lines.insert(0, line)
                if line.strip() == '{':
                    break

            if json_lines:
                json_str = '\n'.join(json_lines)
                return json.loads(json_str)
            else:
                return {"error": "system_integrity_check_no_json_found", "stdout": result.stdout}
        except json.JSONDecodeError as e:
            return {"error": f"system_integrity_check_json_parse_failed: {e}", "stdout": result.stdout}
    except Exception as e:
        return {"error": f"system_integrity_check_exception: {e}"}

def run_data_integrity_check() -> Dict[str, Any]:
    """데이터 무결성 체크 실행"""
    try:
        import subprocess
        result = subprocess.run([
            sys.executable,
            os.path.join(ROOT, "scripts", "data_integrity_check.py")
        ], capture_output=True, text=True, timeout=30)

        # JSON 파싱 시도 (마지막 JSON 블록만 추출)
        try:
            # stdout에서 마지막 JSON 블록 찾기
            lines = result.stdout.strip().split('\n')
            json_lines = []
            in_json = False

            for line in reversed(lines):
                if line.strip() == '}':
                    in_json = True
                if in_json:
                    json_lines.insert(0, line)
                if line.strip() == '{':
                    break

            if json_lines:
                json_str = '\n'.join(json_lines)
                return json.loads(json_str)
            else:
                return {"error": "data_integrity_check_no_json_found", "stdout": result.stdout}
        except json.JSONDecodeError as e:
            return {"error": f"data_integrity_check_json_parse_failed: {e}", "stdout": result.stdout}
    except Exception as e:
        return {"error": f"data_integrity_check_exception: {e}"}

def run_context_guard() -> Dict[str, Any]:
    """컨텍스트 가드 실행"""
    try:
        import subprocess
        result = subprocess.run([
            sys.executable,
            os.path.join(ROOT, "scripts", "context_guard.py")
        ], capture_output=True, text=True, timeout=30)

        # JSON 파싱 시도 (마지막 JSON 블록만 추출)
        try:
            # stdout에서 마지막 JSON 블록 찾기
            lines = result.stdout.strip().split('\n')
            json_lines = []
            in_json = False

            for line in reversed(lines):
                if line.strip() == '}':
                    in_json = True
                if in_json:
                    json_lines.insert(0, line)
                if line.strip() == '{':
                    break

            if json_lines:
                json_str = '\n'.join(json_lines)
                return json.loads(json_str)
            else:
                return {"error": "context_guard_no_json_found", "stdout": result.stdout}
        except json.JSONDecodeError as e:
            return {"error": f"context_guard_json_parse_failed: {e}", "stdout": result.stdout}
    except Exception as e:
        return {"error": f"context_guard_exception: {e}"}

def main():
    parser = argparse.ArgumentParser(description="VELOS System Health MUX")
    parser.add_argument("--output", help="Output JSON file path")
    args = parser.parse_args()

    print("=== VELOS System Health MUX ===")

    # 각 헬스 체크 실행
    system_check = run_system_integrity_check()
    data_check = run_data_integrity_check()
    context_check = run_context_guard()

    # 통합 결과 생성
    health_result = {
        "timestamp": int(time.time()),
        "system_integrity": system_check,
        "data_integrity": data_check,
        "context_guard": context_check,
        "overall_status": "OK"
    }

    # 전체 상태 판단
    errors = []
    if "error" in system_check:
        errors.append(f"system: {system_check['error']}")
    if "error" in data_check:
        errors.append(f"data: {data_check['error']}")
    if "error" in context_check:
        errors.append(f"context: {context_check['error']}")

    if errors:
        health_result["overall_status"] = "ERROR"
        health_result["errors"] = errors
        print(f"❌ Health check failed: {', '.join(errors)}")
        sys.exit(1)
    else:
        print("✅ All health checks passed")

    # 결과 출력
    result_json = json.dumps(health_result, ensure_ascii=False, indent=2)
    print(result_json)

    # 파일로 저장 (지정된 경우)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result_json)
            print(f"Health result saved to: {args.output}")
        except Exception as e:
            print(f"Failed to save health result: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
