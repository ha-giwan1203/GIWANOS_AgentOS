
import openai
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
openai.api_key = os.getenv("OPENAI_API_KEY")

def explain_code(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"❌ 파일이 존재하지 않습니다: {filepath}")
        return

    code = path.read_text(encoding="utf-8")
    prompt = f"""다음은 Python 코드입니다. 이 코드의 전체 기능과 주요 흐름을 한국어로 상세히 설명해 주세요.

```python
{code}
```"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    explanation = response["choices"][0]["message"]["content"]

    out_path = path.with_suffix(".explained.md")
    out_path.write_text(explanation, encoding="utf-8")
    print(f"✅ 설명 파일 저장 완료 → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 사용법: python code_explainer.py 파일이름.py")
    else:
        explain_code(sys.argv[1])
