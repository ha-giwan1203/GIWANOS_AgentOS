# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
# coding: utf-8
"""
velos_bridge.py (BOM-safe + soft-fail)
- 소비 위치:
    1) <ROOT>/data/dispatch/_queue
    2) <ROOT>/data/reports/_dispatch
- 판정 규칙:
    - 채널 전송 성공(True) >= 1개면 OK
    - 전송 자체를 시도 못해서(None=SKIP)만 있었다면 OK
    - 전송을 시도했으나(False) 전부 실패면 FAILED
- UTF-8 with BOM/without BOM 모두 파싱되도록 read_json_any() 적용
"""

import json
import os
import shutil
import time
import traceback
from pathlib import Path

from modules.report_paths import ROOT
INBOXES = [
    ROOT / "data" / "dispatch" / "_queue",
    ROOT / "data" / "reports" / "_dispatch",
]
OUTS = {
    str(ROOT / "data" / "dispatch" / "_queue"): (
        ROOT / "data" / "dispatch" / "_processed",
        ROOT / "data" / "dispatch" / "_failed",
    ),
    str(ROOT / "data" / "reports" / "_dispatch"): (
        ROOT / "data" / "reports" / "_dispatch_processed",
        ROOT / "data" / "reports" / "_dispatch_failed",
    ),
}

LOGDIR = ROOT / "logs"
LOGDIR.mkdir(parents=True, exist_ok=True)
LOG = LOGDIR / "velos_bridge.log"

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)

def try_import(module_name):
    try:
        return __import__(module_name.replace("/", ".").replace("\\", "."))
    except Exception:
        return None

# Optional senders (있으면 사용)
# - scripts/notify_slack_api.py : def send_message(token, channel, text) -> None
# - scripts/notify_slack.py     : def send(text, channel=None, token=None) -> None
# - tools/notion_integration/__init__.py : def send_page(token, parent_id, title, md_content=None) -> None
slack_api    = try_import("scripts.notify_slack_api")
slack_legacy = try_import("scripts.notify_slack")
notion_mod   = try_import("tools.notion_integration")

SLACK_TOKEN  = os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

def send_slack(text, channel=None):
    # True=성공, False=시도 실패, None=시도 불가(SKIP)
    if slack_api and hasattr(slack_api, "send_message") and SLACK_TOKEN and channel:
        try:
            slack_api.send_message(SLACK_TOKEN, channel, text)
            return True
        except Exception as e:
            log(f"Slack 실패: {e}")
            return False
    if slack_legacy and hasattr(slack_legacy, "send"):
        try:
            slack_legacy.send(text, channel=channel, token=SLACK_TOKEN)
            return True
        except Exception as e:
            log(f"Slack(legacy) 실패: {e}")
            return False
    log("SKIP slack: sender/token/channel 미존재")
    return None

def send_notion(title, md_content=None, parent_id=None):
    if notion_mod and hasattr(notion_mod, "send_page") and NOTION_TOKEN and parent_id:
        try:
            notion_mod.send_page(NOTION_TOKEN, parent_id, title, md_content=md_content)
            return True
        except Exception as e:
            log(f"Notion 실패: {e}")
            return False
    log("SKIP notion: sender/token/parent_id 미존재")
    return None

def read_json_any(p: Path):
    # BOM 안전: 우선 utf-8-sig로 시도, 실패 시 utf-8
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return json.loads(p.read_text(encoding="utf-8"))

def process_ticket(p: Path):
    data = read_json_any(p)
    title = data.get("title") or "GIWANOS Update"
    text  = data.get("message") or data.get("text") or ""
    report_md = data.get("report_md")
    channels = data.get("channels") or {}

    success = 0
    attempted = 0

    # Slack
    sl = channels.get("slack") or {}
    if sl.get("enabled"):
        ch = sl.get("channel") or "#general"
        r = send_slack(text, channel=ch)
        if r is True:
            success += 1
        if r is False:
            attempted += 1

    # Notion
    nt = channels.get("notion") or {}
    if nt.get("enabled"):
        parent = nt.get("parent_page_id") or nt.get("database_id")
        r = send_notion(title=title, md_content=report_md or text, parent_id=parent)
        if r is True:
            success += 1
        if r is False:
            attempted += 1

    # 판정: 성공 1개 이상이면 OK, 시도 자체가 없었으면 OK, 그 외(모두 실패) FAILED
    if success >= 1:
        return True
    if attempted == 0:
        return True
    return False

def handle_file(p: Path):
    inbox_key = str(p.parent)
    ok_dir, ng_dir = OUTS[inbox_key]
    ok_dir.mkdir(parents=True, exist_ok=True)
    ng_dir.mkdir(parents=True, exist_ok=True)
    try:
        log(f"처리 시작: {p.name} @ {p.parent}")
        ok = process_ticket(p)
        dst = (ok_dir if ok else ng_dir) / p.name
        shutil.move(str(p), str(dst))
        log(f"처리 결과: {p.name} -> {'OK' if ok else 'FAILED'}")
    except Exception:
        log(f"예외: {p.name} -> FAILED\n{traceback.format_exc()}")
        try:
            shutil.move(str(p), str((ng_dir / p.name)))
        except Exception:
            pass

def main():
    for inbox in INBOXES:
        inbox.mkdir(parents=True, exist_ok=True)
        files = sorted([x for x in inbox.glob("*.json") if x.is_file()])
        if not files:
            log(f"queue 비어있음: {inbox}")
            continue
        for f in files:
            handle_file(f)

if __name__ == "__main__":
    main()
