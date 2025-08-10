# =============================================================================
# 🧠 VELOS 컨텍스트‑기반 의사결정 엔진 (하드코딩 제거 + ChatSyncGuard 연동)
#     경로: C:/giwanos/modules/core/context_aware_decision_engine.py
# =============================================================================
from __future__ import annotations

import os
import sys
from typing import List, Dict

from dotenv import load_dotenv

# 공통 설정/경로
from modules.core.config import BASE_DIR, get_setting
from modules.automation.sync.chat_sync_guard import ChatSyncGuard
# 메모리 검색은 프로젝트 내 실제 구현으로 유지
from modules.core.memory_retriever import search as retrieve_memory  # noqa

# 마스터 루프의 저장 루틴 재사용(파일명 변경 금지)
from scripts.run_giwanos_master_loop import save_dialog_memory

# OpenAI
load_dotenv()
import openai  # type: ignore

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TOP_K_MEMORY = int(os.getenv("TOP_K_MEMORY", get_setting("TOP_K_MEMORY", 5)))
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", get_setting("OPENAI_TEMPERATURE", 0.4)))
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", get_setting("OPENAI_MAX_TOKENS", 800)))
MODEL_NAME = os.getenv("OPENAI_MODEL", get_setting("OPENAI_MODEL", "gpt-4o"))

# 경로 보정
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


def _build_messages(user_prompt: str, recalled: List[Dict]) -> List[Dict]:
    system_msg = {
        "role": "system",
        "content": "당신은 VELOS 시스템의 판단 에이전트입니다."
    }
    mem_block = "\n".join(
        f"[MEM] {m.get('insight','')}" for m in recalled if isinstance(m, dict)
    )
    messages: List[Dict] = [system_msg]
    if mem_block.strip():
        messages.append({"role": "system", "content": mem_block})
    messages.append({"role": "user", "content": user_prompt})
    return messages


def generate_gpt_response(prompt: str) -> str:
    """기존 GPT 호출 함수. 다른 모듈이 이미 사용 중일 수 있어 보존."""
    try:
        recalled = retrieve_memory(prompt, k=TOP_K_MEMORY)
        messages = _build_messages(prompt, recalled)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT 판단 실패: {e}]"


# ────────────────────────────────────────────────────────────────────────────
# ChatSyncGuard 연동 래퍼
_guard = ChatSyncGuard(mirror_slack=True, mirror_notion=True)


def generate_gpt_response_with_guard(prompt: str, conversation_id: str | None = None) -> str:
    def _gpt_call(p: str) -> str:
        return generate_gpt_response(p)

    def _local_save(resp: str) -> bool:
        try:
            save_dialog_memory(resp)
            return True
        except Exception:
            return False

    ok, rsp = _guard.call(prompt, _gpt_call, _local_save, conversation_id=conversation_id)
    if not ok:
        raise RuntimeError(f"ChatSyncGuard failed: {rsp}")
    return rsp  # type: ignore[str-bytes-safe]


# ────────────────────────────────────────────────────────────────────────────
# 자체 검증
def _self_test():
    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY 누락"
    print("[context_aware_decision_engine] self-test OK")


if __name__ == "__main__":
    _self_test()
    print("▶️", generate_gpt_response("시스템 상태를 요약해줘"))
