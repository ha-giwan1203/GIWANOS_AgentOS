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
"""
VELOS-Cursor Interface

VELOS 시스템에서 Cursor 연동 명령을 처리하는 인터페이스입니다.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict

# VELOS 루트 경로 추가
sys.path.append(os.getenv("VELOS_ROOT", r"C:\giwanos"))

# 한국어 환경 설정
os.environ.setdefault("VELOS_LANG", "ko")
os.environ.setdefault("APP_LOCALE", "ko-KR")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# 공용 로거 설정
from modules.core.logger_config import get_velos_logger

from modules.core.velos_command_processor import create_command_processor
from modules.core.memory_adapter import MemoryAdapter


class VELOSCursorInterface:
    """
    VELOS-Cursor 연동 인터페이스

    명령줄과 대화형 모드로 VELOS 명령을 처리합니다.
    """

    def __init__(self):
        """인터페이스 초기화"""
        self.processor = create_command_processor()
        self.memory = MemoryAdapter()
        self.running = True

    def process_command_line(self, command: str) -> Dict:
        """
        명령줄 명령 처리

        Args:
            command: 처리할 명령

        Returns:
            처리 결과
        """
        try:
            result = self.processor.process_command(command)

            # 결과 출력
            if result["success"]:
                print(f"✅ {result.get('message', '명령이 성공적으로 실행되었습니다.')}")
                if "help" in result:
                    print(result["help"])
            else:
                print(f"❌ 오류: {result.get('error', '알 수 없는 오류가 발생했습니다.')}")

            return result
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"명령 처리 중 오류 발생: {str(e)}"
            }
            print(f"❌ {error_result['error']}")
            return error_result

    def interactive_mode(self):
        """대화형 모드 실행"""
        print("🚀 VELOS-Cursor 통합 인터페이스")
        print("대화형 모드가 시작되었습니다. 'quit' 또는 'exit'로 종료하세요.")
        print("'help'로 사용 가능한 명령을 확인하세요.\n")

        while self.running:
            try:
                # 프롬프트 표시
                command = input("VELOS> ").strip()

                if not command:
                    continue

                # 종료 명령
                if command.lower() in ["quit", "exit", "종료"]:
                    print("VELOS-Cursor 인터페이스를 종료합니다.")
                    self.running = False
                    break

                # 명령 처리
                result = self.process_command_line(command)

                # 메모리 동기화
                if result["success"]:
                    self.memory.flush_jsonl_to_json()

            except KeyboardInterrupt:
                print("\n\nVELOS-Cursor 인터페이스를 종료합니다.")
                self.running = False
                break
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {str(e)}")

    def show_status(self):
        """시스템 상태 표시"""
        try:
            # 메모리 통계
            memory_stats = self.memory.get_stats()

            # 명령 히스토리
            history = self.processor.get_command_history()

            print("📊 VELOS-Cursor 시스템 상태")
            print("=" * 50)

            # 안전한 통계 추출 패턴
            buffer_size = memory_stats.get('buffer_size', 0)
            json_records = memory_stats.get('json_records', 0)
            db_records = memory_stats.get('db_records', 0)

            print(f"메모리 버퍼: {buffer_size}개 항목")
            print(f"JSON 레코드: {json_records}개")
            print(f"DB 레코드: {db_records}개")
            print(f"명령 히스토리: {len(history)}개")

            if history:
                print("\n최근 명령:")
                for i, cmd in enumerate(history[-5:], 1):
                    status_icon = "✅" if cmd.get("status") == "completed" else "❌"
                    print(f"  {i}. {status_icon} {cmd['command'][:50]}...")

            print("=" * 50)

        except Exception as e:
            print(f"❌ 상태 조회 실패: {str(e)}")

    def show_help(self):
        """도움말 표시"""
        help_text = """
VELOS-Cursor 통합 시스템 사용법:

1. 명령줄 모드:
   python scripts/velos_cursor_interface.py "명령어"

2. 대화형 모드:
   python scripts/velos_cursor_interface.py --interactive

3. 시스템 상태 확인:
   python scripts/velos_cursor_interface.py --status

사용 가능한 명령:
• 파일 생성: "파일 생성 test.py 'print(\"Hello\")'"
• 파일 수정: "파일 수정 test.py 라인 5 '새로운 내용'"
• 코드 실행: "실행 test.py"
• 워크스페이스 열기: "워크스페이스 열기"
• 파일 정보: "파일 정보 test.py"
• 파일 목록: "파일 목록"

옵션:
  --interactive, -i    대화형 모드 실행
  --status, -s         시스템 상태 표시
  --help, -h           이 도움말 표시
        """
        print(help_text)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="VELOS-Cursor 통합 인터페이스",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python velos_cursor_interface.py "파일 생성 test.py 'print(\"Hello\")'"
  python velos_cursor_interface.py --interactive
  python velos_cursor_interface.py --status
        """
    )

    parser.add_argument(
        "command",
        nargs="?",
        help="실행할 명령 (대화형 모드가 아닌 경우)"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="대화형 모드 실행"
    )

    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="시스템 상태 표시"
    )

    args = parser.parse_args()

    # 인터페이스 생성
    interface = VELOSCursorInterface()

    try:
        if args.status:
            # 상태 표시
            interface.show_status()
        elif args.interactive:
            # 대화형 모드
            interface.interactive_mode()
        elif args.command:
            # 단일 명령 실행
            result = interface.process_command_line(args.command)

            # JSON 출력 (스크립트에서 사용할 경우)
            if os.getenv("VELOS_OUTPUT_JSON"):
                print(json.dumps(result, ensure_ascii=False, indent=2))

            # 종료 코드 설정
            sys.exit(0 if result["success"] else 1)
        else:
            # 기본: 도움말 표시
            interface.show_help()

    except Exception as e:
        print(f"❌ 인터페이스 오류: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
