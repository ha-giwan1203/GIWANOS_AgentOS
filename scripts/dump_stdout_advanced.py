# [ACTIVE] VELOS 표준 출력 고급 덤프 시스템 - 입력 분석 및 덤프 도구
# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

import sys
import json
import os

def setup_utf8():
    """UTF-8 인코딩 설정"""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def analyze_input(s):
    """입력 문자열을 분석합니다."""
    print("=== 입력 분석 ===")
    print(f"길이: {len(s)} 문자")
    print(f"바이트 길이: {len(s.encode('utf-8'))} 바이트")

    # 줄 수 계산
    lines = s.split('\n')
    print(f"줄 수: {len(lines)}")

    # 특수 문자 개수
    cr_count = s.count('\r')
    lf_count = s.count('\n')
    tab_count = s.count('\t')
    esc_count = s.count('\033')

    print(f"CR (\\r): {cr_count}")
    print(f"LF (\\n): {lf_count}")
    print(f"TAB (\\t): {tab_count}")
    print(f"ESC (\\033): {esc_count}")

    # 인코딩 정보
    print(f"입력 인코딩: {sys.stdin.encoding}")
    print(f"출력 인코딩: {sys.stdout.encoding}")

def dump_formats(s):
    """다양한 형태로 입력을 덤프합니다."""
    print("\n=== 다양한 형태로 덤프 ===")

    # REPR 형태
    print("REPR:", repr(s))

    # JSON 형태
    print("JSON:", json.dumps(s, ensure_ascii=False))

    # 16진수 형태
    print("HEX:", ' '.join(f'{ord(c):02X}' for c in s[:100]))  # 처음 100자만

    # 바이트 형태
    print("BYTES:", s.encode('utf-8')[:100])  # 처음 100바이트만

    # 라인별 분석
    print("\n=== 라인별 분석 ===")
    for i, line in enumerate(s.split('\n')[:10]):  # 처음 10줄만
        print(f"라인 {i+1}: {repr(line)}")

def main():
    """메인 함수"""
    setup_utf8()

    print("=== VELOS 표준 입력 덤프 도구 ===")
    print("표준 입력을 읽어서 다양한 형태로 분석합니다.")
    print("입력을 입력하세요 (Ctrl+D 또는 Ctrl+Z로 종료):")

    try:
        s = sys.stdin.read()

        if not s:
            print("입력이 없습니다.")
            return

        analyze_input(s)
        dump_formats(s)

    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()



