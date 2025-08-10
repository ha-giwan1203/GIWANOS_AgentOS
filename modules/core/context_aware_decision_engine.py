# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from typing import List, Dict
from dotenv import load_dotenv; load_dotenv("C:/giwanos/configs/.env")

# 임베딩 검색 + 룸 라우팅
from modules.core.memory_retriever import search as retrieve_memory
from modules.core.chat_rooms import base_room_id

# OpenAI (v1.x)
import openai
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL") or None
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
TOP_K = int(os.getenv("TOP_K_MEMORY", "5"))
MAX_COMP_TOK = int(os.getenv("OPENAI_MAX_TOKENS", "900"))
MAX_SNIPPET = int(os.getenv("MAX_SNIPPET_CHARS", "800"))

def _build_messages(prompt: str, mems: List[Dict]) -> List[Dict]:
    sys = [{"role": "system", "content": "당신은 VELOS 시스템의 판단 에이전트입니다."}]
    if mems:
        block = "\n".join((f"[MEM] {m.get('insight','')}"[:MAX_SNIPPET]) for m in mems if isinstance(m, dict))
        if block.strip():
            sys.append({"role": "system", "content": block})
    return [*sys, {"role": "user", "content": prompt}]

def generate_gpt_response(prompt: str) -> str:
    # 임베딩 기억 가져오기 실패해도 호출은 계속
    try:
        mems = retrieve_memory(prompt, k=TOP_K)
    except Exception:
        mems = []
    msgs = _build_messages(prompt, mems)

    # gpt-5 규격: max_completion_tokens 사용, temperature는 기본값(모델 강제)
    kwargs = dict(model=MODEL, messages=msgs, max_completion_tokens=MAX_COMP_TOK)
    rsp = client.chat.completions.create(**kwargs)
    return (rsp.choices[0].message.content or "").strip()

def generate_gpt_response_with_guard(prompt: str, conversation_id: str | None = None) -> str:
    # ChatSyncGuard 있으면 거쳐서 호출 (Slack 미러/Notion 미러 플래그는 여기서 제어)
    try:
        from modules.automation.sync.chat_sync_guard import ChatSyncGuard
    except Exception:
        return generate_gpt_response(prompt)

    room = conversation_id or base_room_id()
    guard = ChatSyncGuard(mirror_slack=True, mirror_notion=False, conversation_id=room)

    def _call(p: str) -> str:
        return generate_gpt_response(p)

    def _save(r: str) -> bool:
        return isinstance(r, str) and len(r) > 0

    ok, out = guard.call(prompt, _call, _save, conversation_id=room)
    return out if ok else str(out)
