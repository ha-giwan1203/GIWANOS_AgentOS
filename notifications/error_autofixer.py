
import subprocess
import sys
from pathlib import Path
import openai
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
openai.api_key = os.getenv("OPENAI_API_KEY")

def run_python_file(filepath):
    result = subprocess.run(["python", filepath], capture_output=True, text=True)
    return result

def suggest_fix(filepath, stderr_output):
    with open(filepath, encoding="utf-8") as f:
        original_code = f.read()

    prompt = f"""아래는 오류가 발생한 Python 코드입니다. 오류 메시지를 참고하여 코드를 수정해 주세요.

오류 메시지:
{stderr_output}

오리지널 코드:
```python
{original_code}
```

수정된 전체 코드를 아래에 제공해 주세요:"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response["choices"][0]["message"]["content"]

def main():
    if len(sys.argv) < 2:
        print("❌ 사용법: python error_autofixer.py <파일경로>")
        sys.exit(1)

    target_file = sys.argv[1]
    if not Path(target_file).exists():
        print(f"❌ 파일이 존재하지 않습니다: {target_file}")
        sys.exit(1)

    print(f"▶️ {target_file} 실행 중...")
    result = run_python_file(target_file)

    if result.returncode == 0:
        print("✅ 실행 성공: 오류 없음")
    else:
        print("⚠️ 오류 감지됨, 수정 제안 생성 중...")
        fixed = suggest_fix(target_file, result.stderr)
        fixed_path = Path(target_file).with_name("fixed_" + Path(target_file).name)
        with open(fixed_path, "w", encoding="utf-8") as f:
            f.write(fixed)
        print(f"✅ 수정 제안 완료 → {fixed_path}")

if __name__ == "__main__":
    main()
