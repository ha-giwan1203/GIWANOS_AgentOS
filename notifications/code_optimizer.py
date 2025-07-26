
import openai
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
openai.api_key = os.getenv("OPENAI_API_KEY")

def optimize_code(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"❌ 파일이 존재하지 않습니다: {filepath}")
        return

    code = path.read_text(encoding="utf-8")
    prompt = f"""아래 Python 코드를 더 깔끔하고 효율적으로 리팩터링해 주세요.
불필요한 반복, 개선 가능한 변수명, 함수 분리 등도 고려해 주세요.

```python
{code}
```"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    optimized = response["choices"][0]["message"]["content"]

    out_path = path.with_name("opt_" + path.name)
    out_path.write_text(optimized, encoding="utf-8")
    print(f"✅ 최적화 코드 저장 완료 → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 사용법: python code_optimizer.py 파일이름.py")
    else:
        optimize_code(sys.argv[1])
