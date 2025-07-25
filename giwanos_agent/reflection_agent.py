import logging
import os
from datetime import datetime

class ReflectionAgent:
    def __init__(self):
        self.reflection_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reflections'))
        self.md_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reflection_md'))
        os.makedirs(self.reflection_dir, exist_ok=True)
        os.makedirs(self.md_dir, exist_ok=True)

    def create_reflection(self):
        reflection_content = f"Reflection created at {datetime.now()}"
        reflection_filename = datetime.now().strftime("reflection_%Y%m%d_%H%M%S.txt")
        md_filename = datetime.now().strftime("reflection_%Y%m%d_%H%M%S.md")

        with open(os.path.join(self.reflection_dir, reflection_filename), 'w', encoding='utf-8') as f:
            f.write(reflection_content)

        with open(os.path.join(self.md_dir, md_filename), 'w', encoding='utf-8') as f:
            f.write(f"# Reflection\n\n{reflection_content}")

        logging.info(f"Reflection files '{reflection_filename}' and '{md_filename}' created.")