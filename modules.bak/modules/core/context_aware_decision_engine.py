# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# · 이 파일은 “컨텍스트‑기반 의사결정 엔진”으로,
#   저장된 기억을 자동 검색해 GPT‑프롬프트에 삽입합니다.
# · 파일명 / 경로:
#     C:/giwanos/modules/core/context_aware_decision_engine.py
#   (절대 변경 금지)
# · 모든 함수는 자체 검증 로직을 포함해야 합니다.
# =============================================================================

import os, sys, time, json
from typing import List, Dict
from dotenv import load_dotenv
import openai

# ────────────────────────────────────────────────────────────────────────────
# 외부 모듈 경로 보장 (수동 배치 환경 대비)
GIWANOS_ROOT = "C:/giwanos"
if GIWANOS_ROOT not in sys.path:
    sys.path.append(GIWANOS_ROOT)

# 메모리 자동 검색 모듈
from modules.core.memory_retriever import search as retrieve_memory   # noqa

load_dotenv()                           # .env 로드
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ────────────────────────────────────────────────────────────────────────────
# 설정
TOP_K_MEMORY = 5                        # 프롬프트에 삽입할 기억 개수
TEMPERATURE  = 0.4
MAX_TOKENS   = 800

# ────────────────────────────────────────────────────────────────────────────
def _build_messages(user_prompt: str,
                    recalled: List[Dict]) -> List[Dict]:
    """
    GPT‑4o 입력용 messages 리스트를 구성한다.
    """
    system_msg = {
        "role": "system",
        "content": "당신은 VELOS 시스템의 판단 에이전트입니다."
    }

    mem_block = "\n".join(
        f"[MEM] {m['insight']}" for m in recalled
    )
    messages: List[Dict] = [system_msg]

    if mem_block.strip():
        messages.append({
            "role": "system",
            "content": mem_block
        })

    messages.append({"role": "user", "content": user_prompt})
    return messages


def generate_gpt_response(prompt: str) -> str:
    """
    - prompt       : 사용자 입력
    - return value : GPT‑4o 응답 문자열
    """
    try:
        print("🧠 기억 검색 중…")
        recalled = retrieve_memory(prompt, k=TOP_K_MEMORY)
        print(f"   ↳ {len(recalled)}개 기억 recall 완료")

        messages = _build_messages(prompt, recalled)

        print("🧠 GPT API 호출 중…")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        output = response.choices[0].message.content
        print("✅ GPT 응답 완료")
        return output.strip()

    except Exception as e:
        print(f"❌ GPT 호출 실패: {e}")
        return "[GPT 판단 실패 – 예외 발생]"


# ────────────────────────────────────────────────────────────────────────────
# 자체 검증 (문법·기억·API 키 존재 여부)
def _self_test():
    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY 환경변수가 없습니다."

    demo_q = "파일명 절대 바꾸지 마라는 지시를 기억하고 있나요?"
    recalled = retrieve_memory(demo_q, 3)
    assert recalled, "메모리 검색 결과가 없습니다."
    assert {"from", "insight", "tags"}.issubset(recalled[0].keys()), \
        "메모리 필드 누락"

    print("[context_aware_decision_engine] self‑test ‑ OK",
          f"({len(recalled)} records)")

if __name__ == "__main__":
    _self_test()
    demo_out = generate_gpt_response("시스템 상태를 요약해줘")
    print("▶️ GPT 응답:", demo_out)


