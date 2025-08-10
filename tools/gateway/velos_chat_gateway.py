# -*- coding: utf-8 -*-
from __future__ import annotations
import os, uvicorn, json, time
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from pathlib import Path
from modules.core.chat_rooms import base_room_id
from modules.core.context_aware_decision_engine import generate_gpt_response_with_guard

API_KEY = os.getenv("VELOS_CHAT_API_KEY","")
CHAT_DIR = Path("C:/giwanos/data/chat"); CHAT_DIR.mkdir(parents=True, exist_ok=True)
app = FastAPI()

def _auth(req: Request):
    if API_KEY and req.headers.get("X-VELOS-Key") != API_KEY:
        raise HTTPException(401, "unauthorized")

@app.post("/chat/send")
async def send(req: Request):
    _auth(req)
    body = await req.json()
    text = (body.get("text") or "").strip()
    room = (body.get("room_id") or base_room_id())[:24]
    if not text: raise HTTPException(400, "text required")
    out = generate_gpt_response_with_guard(text, conversation_id=room)
    return {"ok": True, "room_id": room, "reply": out}

@app.get("/chat/history")
async def history(req: Request, room_id: str, tail: int = 50):
    _auth(req)
    p = CHAT_DIR / f"chat_{room_id}.jsonl"
    if not p.exists(): return []
    lines = p.read_text(encoding="utf-8").splitlines()[-tail:]
    return [json.loads(x) for x in lines if x.strip()]

@app.websocket("/ws/chat")
async def ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_json()
            text = (msg.get("text") or "").strip()
            room = (msg.get("room_id") or base_room_id())[:24]
            out = generate_gpt_response_with_guard(text, conversation_id=room)
            await ws.send_json({"room_id": room, "reply": out, "ts": time.time()})
    except WebSocketDisconnect:
        return

if __name__ == "__main__":
    uvicorn.run("tools.gateway.velos_chat_gateway:app",
                host=os.getenv("GATEWAY_HOST","127.0.0.1"),
                port=int(os.getenv("GATEWAY_PORT","8787")),
                reload=False)
