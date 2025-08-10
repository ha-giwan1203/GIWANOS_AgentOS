
import sys
import py_compile
import os

def check_syntax(filepath):
    if not os.path.exists(filepath):
        print(f"❌ 파일이 존재하지 않습니다: {filepath}")
        return

    print(f"🔍 문법 검사 중: {filepath}")
    try:
        py_compile.compile(filepath, doraise=True)
        print("✅ 문법 오류 없음 - 정상 파일입니다.")
    except py_compile.PyCompileError as e:
        print("❌ 문법 오류 발생:")
        print(e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python check_syntax.py [파일 경로]")
    else:
        check_syntax(sys.argv[1])


