from datetime import datetime
import json
from pathlib import Path

GIWANOS_ROOT = Path("C:/giwanos")

# 명확한 경로 참조 (judgment_rules.json)
def load_judgment_rules():
    rules_path = GIWANOS_ROOT / "core" / "judgment_rules.json"
    with open(rules_path, "r", encoding="utf-8") as file:
        return json.load(file)

# 회고 텍스트 파일 정확한 생성 및 저장
def generate_reflection(content):
    reflections_dir = GIWANOS_ROOT / "data" / "reflections"
    reflections_dir.mkdir(parents=True, exist_ok=True)
    
    reflection_filename = datetime.now().strftime("reflection_%Y%m%d_%H%M%S.md")
    reflection_path = reflections_dir / reflection_filename

    with open(reflection_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Reflection saved at: {reflection_path}")

# 예시 사용
def main():
    rules = load_judgment_rules()
    reflection_content = "# Daily Reflection\n\nGenerated rules count: " + str(len(rules))
    generate_reflection(reflection_content)

if __name__ == "__main__":
    main()

