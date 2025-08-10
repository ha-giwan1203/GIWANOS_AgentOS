# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, time, threading
from pathlib import Path
from typing import Callable, Tuple

AUDIT_LOG = Path("C:/giwanos/data/logs/chat_sync_audit.jsonl")
CHAT_DIR  = Path("C:/giwanos/data/chat"); CHAT_DIR.mkdir(parents=True, exist_ok=True)
_lock = threading.Lock()

def _writeln(p: Path, rec: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _room_file(room_id: str) -> Path:
    return CHAT_DIR / f"chat_{room_id}.jsonl"

def _append_with_lock(p: Path, rec: dict, retries: int = 3, backoff: float = 0.2) -> bool:
    for i in range(retries):
        try:
            with _lock:
                with p.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            time.sleep(backoff * (2**i))
    return False

class ChatSyncGuard:
    def __init__(self, mirror_slack: bool = True, mirror_notion: bool = False, conversation_id: str | None = None):
        self.mirror_slack = mirror_slack
        self.mirror_notion = mirror_notion
        self.conversation_id = conversation_id

    def call(self, prompt: str,
             gpt_call: Callable[[str], str],
             local_save: Callable[[str], bool],
             conversation_id: str | None = None) -> Tuple[bool, str]:
        room_id = conversation_id or self.conversation_id
        if not room_id:
            raise ValueError("conversation_id is required to avoid session drift")

        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        chat_file = _room_file(room_id)

        # 1) 입력 저장
        ok1 = _append_with_lock(chat_file, {"ts": ts, "room_id": room_id, "role": "user", "text": prompt, "meta": {"source": "local"} })
        # 2) GPT 호출
        try:
            rsp = gpt_call(prompt)
            ok2 = True
        except Exception as e:
            rsp = f"[gpt_error] {e}"
            ok2 = False
        # 3) 출력 저장
        ok3 = _append_with_lock(chat_file, {"ts": ts, "room_id": room_id, "role": "assistant", "text": rsp, "meta": {"source": "local"} })

        # 4) 로컬 세이브 훅
        ok4 = False
        try:
            ok4 = local_save(rsp)
        except Exception:
            ok4 = False

        # 감사 로그
        _writeln(AUDIT_LOG, {"ts": ts, "room_id": room_id, "step":"done", "save_in": ok1, "gpt": ok2, "save_out": ok3, "local_save": ok4})
        return (ok2 and ok1 and ok3), rsp

