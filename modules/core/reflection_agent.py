
import logging
import sys
from datetime import datetime
from pathlib import Path
from openai import OpenAI
import os, json
from dotenv import load_dotenv

load_dotenv("C:/giwanos/config/.env")

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('C:/giwanos/data/logs/reflection_agent.log'),
        logging.StreamHandler(sys.stdout)
    ],
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def load_system_status():
    try:
        with open("C:/giwanos/data/logs/system_health.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"시스템 상태 로드 중 오류: {e}")
        return {}

def generate_adaptive_reflection():
    logging.info("🧠 실제 시스템 데이터를 포함한 유연한 자동 회고 생성 시작")
    try:
        system_status = load_system_status()

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 GIWANOS 시스템의 자동 회고 에이전트입니다. 제공된 실제 시스템 상태 및 로그 데이터를 분석하여 유연하고 구체적인 자동 회고 메시지를 작성해 주세요."},
                {"role": "user", "content": f"오늘의 실제 시스템 상태 데이터는 다음과 같습니다:\n{json.dumps(system_status, ensure_ascii=False, indent=2)}\n\n이를 기반으로 오늘의 유연한 자동 회고를 작성해주세요."}
            ],
            max_tokens=700,
            temperature=0.6
        )

        reflection_content = response.choices[0].message.content.strip()

        reflection_dir = Path("C:/giwanos/data/reflections")
        reflection_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Markdown(.md) 파일 저장
        md_path = reflection_dir / f"adaptive_reflection_{timestamp}.md"
        md_path.write_text(reflection_content, encoding='utf-8')

        # 텍스트(.txt) 파일 저장
        txt_path = reflection_dir / f"adaptive_reflection_{timestamp}.txt"
        txt_path.write_text(reflection_content, encoding='utf-8')

        logging.info(f"✅ 실제 데이터 기반 유연한 회고 생성 완료: {md_path}, {txt_path}")

        print("\n[📌 유연한 자동 회고 파일 내용 출력]")
        print(reflection_content)
        print("[📌 회고 파일 출력 완료]\n")

    except Exception as e:
        logging.error(f"유연한 회고 생성 중 오류 발생: {e}")

def run_reflection():
    generate_adaptive_reflection()

if __name__ == '__main__':
    run_reflection()
