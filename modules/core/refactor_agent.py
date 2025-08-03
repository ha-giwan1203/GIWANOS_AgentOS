
import logging
import sys
import os
from datetime import datetime

logger = logging.getLogger("refactor_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/refactor_recommendations.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def generate_refactor_recommendations():
    recommendations_path = "C:/giwanos/data/logs/refactor_recommendations.md"
    recommendations = [
        {
            "file": "modules/core/some_module.py",
            "recommendation": "반복 코드 발견, 함수화 필요"
        },
        {
            "file": "modules/core/another_module.py",
            "recommendation": "함수가 너무 큼, 분할 필요"
        }
    ]

    with open(recommendations_path, 'w', encoding='utf-8') as md_file:
        md_file.write("# 🔍 리팩토링 추천 (자동 생성)\n\n")
        for rec in recommendations:
            md_file.write(f"- **파일명**: {rec['file']}\n")
            md_file.write(f"- **추천 사항**: {rec['recommendation']}\n\n")

    logger.info("리팩토링 추천 사항이 정상적으로 생성되었습니다.")

if __name__ == '__main__':
    generate_refactor_recommendations()
