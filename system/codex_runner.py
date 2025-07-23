
import subprocess
import sys

MENU = {
    "1": ("오류 자동 수정 (error_autofixer)", "error_autofixer.py"),
    "2": ("전체 검사 및 수정 (check_and_fix_all)", "check_and_fix_all.py"),
    "3": ("코드 설명 생성 (code_explainer)", "code_explainer.py"),
    "4": ("docstring 자동 생성 (docstring_writer)", "docstring_writer.py"),
    "5": ("코드 최적화 (code_optimizer)", "code_optimizer.py"),
    "6": ("문서화 (.md 생성) (generate_code_docs)", "generate_code_docs.py"),
    "0": ("종료", None)
}

def main():
    while True:
        print("\n🧠 Codex 도구 실행기 (advanced_modules)")
        for key, (desc, _) in MENU.items():
            print(f"[{key}] {desc}")
        choice = input("실행할 작업 번호를 선택하세요: ").strip()

        if choice not in MENU:
            print("❌ 잘못된 선택입니다.")
            continue
        if choice == "0":
            break

        script = MENU[choice][1]
        try:
            subprocess.run(["python", f"advanced_modules/{script}"], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ {script} 실행 중 오류 발생")

if __name__ == "__main__":
    main()
