
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SRC_DIR = Path(".")

py_files = [f for f in SRC_DIR.glob("*.py") if not f.name.startswith(("doc_", "opt_", "fixed_"))]

for file in py_files:
    print(f"🧾 문서화 중: {file.name}")
    code = file.read_text(encoding="utf-8")

    prompt = f"""다음 Python 파일을 마크다운 형식으로 문서화해 주세요.
코드의 목적, 주요 함수, 흐름 등을 정리해 주세요.

```python
{code}
```"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    md = response.choices[0].message.content
    print(f"📄 문서화 결과 ↓↓↓\n")
    print(md)
    print(f"🧾 {file.name} 문서 출력 완료\n{'-'*60}")
