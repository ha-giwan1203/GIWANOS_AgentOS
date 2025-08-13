import re
import pathlib

ROOT = pathlib.Path(r"C:\giwanos\scripts")

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
