# [ACTIVE] VELOS Bridge - 메시지 디스패치 시스템
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

import os, sys
HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 환경 변수 로드
try:
    from dotenv import load_dotenv
    env_file = os.path.join(ROOT, "configs", ".env")
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file, override=True)
        print(f"[INFO] 환경 설정 로드: {env_file}")
except ImportError:
    print("[WARN] python-dotenv not installed")
except Exception as e:
    print(f"[WARN] 환경 설정 로드 실패: {e}")

try:
    from modules.report_paths import ROOT as REPORT_ROOT
except Exception as e:
    # 최소한의 디버그
    print("[WARN] import modules.report_paths failed:", e)
    # 필요시 대체 경로 지정
    REPORT_ROOT = ROOT

# 작업 폴더도 루트로 고정
try:
    os.chdir(ROOT)
except Exception:
    pass

import json
import shutil
import time
import traceback
from pathlib import Path

# ROOT는 위에서 설정됨
INBOXES = [
    Path(ROOT) / "data" / "dispatch" / "_queue",
    Path(ROOT) / "data" / "reports" / "_dispatch",
]
OUTS = {
    str(Path(ROOT) / "data" / "dispatch" / "_queue"): (
        Path(ROOT) / "data" / "dispatch" / "_processed",
        Path(ROOT) / "data" / "dispatch" / "_failed",
    ),
    str(Path(ROOT) / "data" / "reports" / "_dispatch"): (
        Path(ROOT) / "data" / "reports" / "_dispatch_processed",
        Path(ROOT) / "data" / "reports" / "_dispatch_failed",
    ),
}

LOGDIR = Path(ROOT) / "logs"
LOGDIR.mkdir(parents=True, exist_ok=True)
LOG = LOGDIR / "velos_bridge.log"

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)

def try_import(module_name):
    try:
        # 더 정확한 모듈 import
        from importlib import import_module
        return import_module(module_name.replace("/", ".").replace("\\", "."))
    except Exception as e:
        log(f"[DEBUG] 모듈 import 실패 {module_name}: {e}")
        return None

# Optional senders (있으면 사용)
# - scripts/notify_slack_api.py : def send_message(token, channel, text) -> None
# - scripts/notify_slack.py     : def send(text, channel=None, token=None) -> None
# - tools/notion_integration/__init__.py : def send_page(token, parent_id, title, md_content=None) -> None
# - scripts/dispatch_email.py : def send_email(subject, body, recipients=None, attachment_path=None) -> None
# - scripts/dispatch_push.py : def send_push(title, message, token=None) -> None
slack_api    = try_import("scripts.notify_slack_api")
slack_legacy = try_import("scripts.notify_slack")
notion_mod   = try_import("tools.notion_integration")
email_mod    = try_import("scripts.dispatch_email")
push_mod     = try_import("scripts.dispatch_push")

SLACK_TOKEN  = os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST") 
EMAIL_SMTP_PORT = os.getenv("EMAIL_SMTP_PORT")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS")  # 쉼표로 구분된 이메일 목록
PUSHBULLET_TOKEN = os.getenv("PUSHBULLET_TOKEN")

def send_slack(text, channel=None, file_path=None):
    # True=성공, False=시도 실패, None=시도 불가(SKIP)
    if not SLACK_TOKEN or not channel:
        log("SKIP slack: token/channel 미존재")
        return None
    
    try:
        # 파일 업로드가 요청된 경우
        if file_path and Path(file_path).exists():
            if slack_api and hasattr(slack_api, "send_report"):
                try:
                    result = slack_api.send_report(Path(file_path), title="VELOS Report", comment=text)
                    if result:
                        log(f"Slack 파일 업로드 성공: {file_path}")
                        return True
                    else:
                        log(f"Slack 파일 업로드 실패, 메시지만 전송")
                        # 파일 업로드 실패시 메시지만 전송
                except Exception as e:
                    log(f"Slack 파일 업로드 오류: {e}, 메시지만 전송")
        
        # 메시지 전송 (파일 없거나 업로드 실패시)
        if slack_api and hasattr(slack_api, "send_text"):
            try:
                slack_api.send_text(channel, text)
                log(f"Slack 메시지 전송 성공")
                return True
            except Exception as e:
                log(f"Slack 메시지 전송 실패: {e}")
                return False
        
        # Legacy 방식 fallback
        if slack_legacy and hasattr(slack_legacy, "send"):
            try:
                slack_legacy.send(text, channel=channel, token=SLACK_TOKEN)
                log(f"Slack(legacy) 전송 성공")
                return True
            except Exception as e:
                log(f"Slack(legacy) 실패: {e}")
                return False
                
    except Exception as e:
        log(f"Slack 전송 전체 오류: {e}")
        return False
    
    log("SKIP slack: 사용 가능한 sender 없음")
    return None

def send_notion(title, md_content=None, parent_id=None):
    if notion_mod and hasattr(notion_mod, "send_page") and NOTION_TOKEN:
        try:
            # parent_id가 없으면 기본 페이지에 생성 시도
            notion_mod.send_page(NOTION_TOKEN, parent_id, title, md_content=md_content)
            log(f"Notion 페이지 생성 성공: {title}")
            return True
        except Exception as e:
            log(f"Notion 실패: {e}")
            return False
    log("SKIP notion: sender/token 미존재")
    return None

def send_email(title, content, recipients=None, file_path=None):
    if not email_mod or not EMAIL_SMTP_HOST or not EMAIL_USER:
        log("SKIP email: sender/config 미존재")
        return None
    
    try:
        # recipients가 지정되지 않으면 환경변수에서 가져옴
        if not recipients and EMAIL_RECIPIENTS:
            recipients = [r.strip() for r in EMAIL_RECIPIENTS.split(",")]
        
        if not recipients:
            log("SKIP email: recipients 미존재")
            return None
            
        if hasattr(email_mod, "send_email"):
            result = email_mod.send_email(
                subject=title,
                body=content,
                recipients=recipients,
                attachment_path=file_path if file_path and Path(file_path).exists() else None
            )
            if result:
                log(f"Email 전송 성공: {len(recipients)}명")
                return True
            else:
                log("Email 전송 실패")
                return False
    except Exception as e:
        log(f"Email 전송 오류: {e}")
        return False
    
    log("SKIP email: 전송 함수 없음")
    return None

def send_pushbullet(title, content):
    if not push_mod or not PUSHBULLET_TOKEN:
        log("SKIP pushbullet: sender/token 미존재")
        return None
        
    try:
        if hasattr(push_mod, "send_push"):
            result = push_mod.send_push(title, content, PUSHBULLET_TOKEN)
            if result:
                log(f"PushBullet 전송 성공")
                return True
            else:
                log("PushBullet 전송 실패")
                return False
    except Exception as e:
        log(f"PushBullet 전송 오류: {e}")
        return False
    
    log("SKIP pushbullet: 전송 함수 없음") 
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
        file_path = data.get("file_path") if sl.get("upload_file") else None
        r = send_slack(text, channel=ch, file_path=file_path)
        if r is True:
            success += 1
        if r is False:
            attempted += 1

    # Notion
    nt = channels.get("notion") or {}
    if nt.get("enabled"):
        parent = nt.get("parent_id") or nt.get("parent_page_id") or nt.get("database_id")
        r = send_notion(title=title, md_content=report_md or text, parent_id=parent)
        if r is True:
            success += 1
        if r is False:
            attempted += 1

    # Email
    em = channels.get("email") or {}
    if em.get("enabled"):
        recipients = em.get("recipients")
        file_path = data.get("file_path") if em.get("attach_file") else None
        r = send_email(title=title, content=text, recipients=recipients, file_path=file_path)
        if r is True:
            success += 1
        if r is False:
            attempted += 1

    # PushBullet
    pb = channels.get("pushbullet") or {}
    if pb.get("enabled"):
        r = send_pushbullet(title=title, content=text)
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
