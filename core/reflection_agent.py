
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class ReflectionAgent:
    def __init__(self):
        self.reflections_dir = "C:/giwanos/data/reflections"
        os.makedirs(self.reflections_dir, exist_ok=True)

    def create_reflection(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reflection_content = f"Reflection created at {datetime.now()}"
        
        txt_filename = f"reflection_{timestamp}.txt"
        md_filename = f"reflection_{timestamp}.md"

        # 텍스트(.txt) 파일 저장
        with open(os.path.join(self.reflections_dir, txt_filename), 'w', encoding='utf-8') as txt_file:
            txt_file.write(reflection_content)

        # Markdown(.md) 파일 저장
        with open(os.path.join(self.reflections_dir, md_filename), 'w', encoding='utf-8') as md_file:
            md_file.write(f"# Reflection\n\n{reflection_content}")

        logging.info(f"[성공] Reflection files '{txt_filename}' and '{md_filename}' created.")
        print(f"[✅ 성공] Reflection 저장 완료: {txt_filename}, {md_filename}")

# 예제 실행 코드
if __name__ == "__main__":
    agent = ReflectionAgent()
    agent.create_reflection()
