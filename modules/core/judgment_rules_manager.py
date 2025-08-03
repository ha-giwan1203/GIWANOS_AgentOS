"""
File: C:/giwanos/core/judgment_rules_manager.py

설명:
- JSON 로딩 오류 발생 시 즉시 generate_rules() 호출하여 재생성
- 오류 발생 시 ToolManager.send_notification으로 사용자에게 알림
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import openai
from core.tool_manager import ToolManager

# .env 로드
ROOT_DIR = Path(__file__).parents[1]
dotenv_path = ROOT_DIR / 'config' / '.env'
load_dotenv(dotenv_path=dotenv_path)
openai.api_key = os.getenv('OPENAI_API_KEY')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# 판단 규칙 JSON 파일 경로
RULES_PATH = ROOT_DIR / 'config' / 'judgment_rules.json'

def generate_rules():
    """새 판단 규칙 JSON 생성 및 저장"""
    logging.info(f"Generating new judgment rules at {RULES_PATH}")
    prompt = (
        "다음 기준에 따라 판단 규칙을 JSON 형식으로 생성해주세요:\n"
        "1. 'id': 고유 식별자 (문자열)\n"
        "2. 'description': 규칙 설명 (문자열)\n"
        "3. 'conditions': 조건 객체 (필드명과 기대 타입/값)\n"
        "4. 'actions': 수행할 동작 목록 (문자열 배열)\n"
        "출력은 오직 JSON 구조로만 해주세요."
    )
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a rule-generation assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    clean = content.strip('`')
    try:
        rules = json.loads(clean)
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error during generation: {e}")
        ToolManager.send_notification(f"Error generating rules: {e}")
        raise
    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved judgment rules to: {RULES_PATH}")
    return rules

def load_rules():
    """로컬 파일에서 규칙 로드, 오류 시 재생성 및 알림"""
    if not RULES_PATH.exists():
        return generate_rules()
    try:
        with open(RULES_PATH, encoding="utf-8") as f:
            rules = json.load(f)
        logging.info("Judgment rules loaded from file.")
        return rules
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON file: {e}")
        ToolManager.send_notification(f"Invalid JSON at {RULES_PATH}: regenerating rules.")
        return generate_rules()
    except Exception as e:
        logging.error(f"Unexpected error loading rules: {e}")
        ToolManager.send_notification(f"Error loading rules: {e}")
        return generate_rules()

if __name__ == "__main__":
    rules = load_rules()
    print("Current judgment rules:")
    print(json.dumps(rules, ensure_ascii=False, indent=2))
