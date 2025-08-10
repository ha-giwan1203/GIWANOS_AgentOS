"""
VELOS 운영 철학 선언문
- 파일명 절대 변경 금지 · 모든 수정 후 자가 검증 필수 · 실행 결과 직접 테스트
"""
from __future__ import annotations

import time
import json
import uuid
from typing import Any, Callable, Optional

from modules.core.config import LOG_DIR
from .sync_backends import SlackMirror, NotionMirror

AUDIT_LOG = (LOG_DIR / "chat_sync_audit.jsonl")
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


class ChatSyncGuard:
    """
    GPT 호출을 트랜잭션으로 감싸서
    1) GPT 응답 수신
    2) 로컬 저장 확인(콜백)
    3) 외부 미러(슬랙/노션) 반영
    4) 실패 시 지수 백오프로 재시도
    를 보장한다.
    """

    def __init__(self, mirror_slack: bool = True, mirror_notion: bool = True, max_retries: int = 3):
        self.slack = SlackMirror() if mirror_slack else None
        self.notion = NotionMirror() if mirror_notion else None
        self.max_retries = max_retries

    def _audit(self, record: dict[str, Any]) -> None:
        record["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def call(
        self,
        prompt: str,
        gpt_call: Callable[[str], str],
        local_save: Callable[[str], bool],
        conversation_id: Optional[str] = None,
    ) -> tuple[bool, Any]:
        txid = str(uuid.uuid4())
        cid = conversation_id or f"conv-{time.strftime('%Y%m%d')}"
        backoff = 1.0

        for attempt in range(1, self.max_retries + 1):
            try:
                # 1) GPT
                rsp = gpt_call(prompt)
                self._audit({"txid": txid, "step": "gpt_response", "ok": True, "attempt": attempt})

                # 2) 로컬 저장 확인
                if not local_save(rsp):
                    raise RuntimeError("Local save verification failed")
                self._audit({"txid": txid, "step": "local_save", "ok": True})

                # 3) 외부 미러
                mirror_ok = True
                if self.slack:
                    mirror_ok &= self.slack.mirror(cid, prompt, rsp)
                if self.notion:
                    mirror_ok &= self.notion.mirror(cid, prompt, rsp)
                if not mirror_ok:
                    raise RuntimeError("Mirror verification failed")
                self._audit({"txid": txid, "step": "mirror", "ok": True})

                # 4) 성공
                self._audit({"txid": txid, "step": "done", "ok": True})
                return True, rsp

            except Exception as e:
                self._audit({"txid": txid, "step": "error", "ok": False, "attempt": attempt, "err": str(e)})
                if attempt >= self.max_retries:
                    return False, {"error": str(e)}
                time.sleep(backoff)
                backoff *= 2.0
