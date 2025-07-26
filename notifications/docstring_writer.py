
import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_docstrings(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"❌ 파일이 존재하지 않습니다: {filepath}")
        return

    code = path.read_text(encoding="utf-8")
    prompt = f"""다음 Python 코드에서 각 함수에 적절한 docstring을 추가해 주세요.
기존 코드 스타일은 유지하면서 docstring만 보완된 전체 코드를 반환해 주세요.

```python
{code}
```"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    updated_code = response.choices[0].message.content

    out_path = path.with_name("doc_" + path.name)
    out_path.write_text(updated_code, encoding="utf-8")
    print(f"✅ 주석 추가 완료 → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 사용법: python docstring_writer.py 파일이름.py")
    else:
        generate_docstrings(sys.argv[1])
