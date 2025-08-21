# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=/home/user/webapp 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
import pathlib
import re

from modules.report_paths import P, P`nROOT, "scripts", =

# requests.get/post/put(...) 호출만 잡는다. 중첩 괄호는 안 다루지만 이 코드베이스엔 충분.
CALL = re.compile(
    r"""\brequests\.(?P<fn>get|post|put)\(\s*(?P<args>[^()]*)\)""",
    re.X | re.S,
)


def fix_call(args: str) -> str:
    # 1) "timeout=..., "가 맨 앞에 박힌 바보 패턴 제거
    args = re.sub(r"^\s*timeout\s*=\s*[^,]+,\s*", "", args)
    # 2) 이미 timeout= 있으면 그대로
    if re.search(r"\btimeout\s*=", args):
        return args.strip()
    # 3) 없으면 끝에 timeout=15 추가
    a = args.strip()
    return "timeout=15" if not a else a + ", timeout=15"


def patch_text(src: str) -> str:
    def repl(m):
        args = m.group("args")
        fixed = fix_call(args)
        return f"requests.{m.group('fn')}({fixed})"

    return CALL.sub(repl, src)


def should_skip(p: pathlib.Path) -> bool:
    parts = set(p.parts)
    return "__pycache__" in parts or "db_migrations" in parts


def main():
    patched = 0
    for p in ROOT.rglob("*.py"):
        if should_skip(p):
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        new = patch_text(txt)
        if new != txt:
            p.write_text(new, encoding="utf-8")
            print("[patched-timeout]", p)
            patched += 1
    print(f"[summary] files_patched={patched}")


if __name__ == "__main__":
    main()
