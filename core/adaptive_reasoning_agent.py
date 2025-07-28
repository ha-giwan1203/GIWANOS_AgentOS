import logging
import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# 환경 설정 로드
load_dotenv("C:/giwanos/config/.env")

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('C:/giwanos/data/logs/adaptive_reasoning_agent.log'),
        logging.StreamHandler()
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

def adaptive_reasoning_main():
    logging.info("🧠 Adaptive Reasoning Agent 실행 시작")

    system_status = load_system_status()
    if not system_status:
        logging.warning("시스템 상태 데이터가 없어 기본 추론 메시지를 생성합니다.")
        system_status_info = "시스템 상태 데이터가 없습니다. 기본 상태 메시지를 생성합니다."
    else:
        system_status_info = json.dumps(system_status, ensure_ascii=False, indent=2)

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 GIWANOS 시스템의 Adaptive Reasoning Agent입니다. 시스템의 실시간 상태 데이터를 분석하여 유연하고 창의적인 문제 해결 및 최적화 방안을 제시해주세요."},
                {"role": "user", "content": f"다음은 현재 시스템의 실시간 상태 데이터입니다:\n\n{system_status_info}\n\n이 데이터를 기반으로 시스템 최적화 및 문제해결을 위한 유연한 추론 메시지를 작성해 주세요."}
            ],
            max_tokens=800,
            temperature=0.7
        )

        reasoning_result = response.choices[0].message.content.strip()

        reasoning_dir = Path("C:/giwanos/data/reflections")
        reasoning_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Markdown 파일 저장
        md_path = reasoning_dir / f"adaptive_reasoning_{timestamp}.md"
        md_path.write_text(reasoning_result, encoding='utf-8')

        # 텍스트 파일 저장
        txt_path = reasoning_dir / f"adaptive_reasoning_{timestamp}.txt"
        txt_path.write_text(reasoning_result, encoding='utf-8')

        logging.info(f"✅ Adaptive Reasoning 결과 파일 생성 완료: {md_path}, {txt_path}")

        # 결과 콘솔 출력
        print("\n[🔍 Adaptive Reasoning Agent 결과]")
        print(reasoning_result)
        print("[🔍 Adaptive Reasoning 출력 완료]\n")

    except Exception as e:
        logging.error(f"Adaptive Reasoning Agent 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    adaptive_reasoning_main()
