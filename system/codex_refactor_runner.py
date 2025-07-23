
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def refactor_codex_style(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"❌ 파일이 존재하지 않습니다: {filepath}")
        return

    code = path.read_text(encoding="utf-8")

    prompt = f"""다음 Python 코드를 Codex 기준에 맞춰 리팩터링 해주세요.
- 함수 구조 분리
- 직관적인 변수명
- 예외 처리
- 주석 포함
- 가독성과 유지보수성을 고려한 설계

전체 리팩터링된 코드를 제공해 주세요:

```python
{code}
```"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    result = response.choices[0].message.content
    out_path = path.with_name("codex_" + path.name)
    out_path.write_text(result, encoding="utf-8")
    print(f"✅ Codex 스타일로 리팩터링 완료 → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ 사용법: python codex_refactor_runner.py 파일이름.py")
    else:
        refactor_codex_style(sys.argv[1])
