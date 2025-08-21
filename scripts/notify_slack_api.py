# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=/home/user/webapp 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import requests

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # 없는 환경에서도 돌아가게

# ----- 고정 경로 및 .env 로드 -----
from modules.report_paths import ROOT

ENV = ROOT / "configs" / ".env"
if load_dotenv and ENV.exists():
    load_dotenv(dotenv_path=str(ENV))

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "").strip()
RAW_CHANNEL = (
    os.getenv("SLACK_CHANNEL_ID")
    or os.getenv("SLACK_SUMMARY_CH")
    or os.getenv("SLACK_CHANNEL")
    or ""
).strip()

if not SLACK_BOT_TOKEN or not RAW_CHANNEL:
    print("[ERROR] SLACK_BOT_TOKEN/채널 설정 누락")
    sys.exit(1)

API = "https://slack.com/api"
SESSION = requests.Session()
SESSION.headers.update({"Authorization": f"Bearer {SLACK_BOT_TOKEN}"})


def _mime(p: Path) -> str:
    return mimetypes.guess_type(p.name)[0] or "application/octet-stream"


def _ready(p: Path, tries: int = 6) -> bool:
    last = -1
    for _ in range(tries):
        if not p.exists():
            time.sleep(0.5)
            continue
        sz = p.stat().st_size
        if sz > 0 and sz == last:
            return True
        last = sz
        time.sleep(0.5)
    return p.exists() and p.stat().st_size > 0


def resolve_channel_id(raw: str) -> str:
    # U... 이면 DM 채널(D...)로 변환
    if raw.startswith(("C", "G", "D")):
        return raw
    if raw.startswith("U"):
        r = SESSION.post(f"{API}/conversations.open", data={"users": raw})
        j = (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else {"ok": False, "raw": r.text}
        )
        if j.get("ok") and "channel" in j:
            ch = j["channel"]["id"]
            print(f"[INFO] 사용자 ID → DM 채널 변환: {raw} → {ch}")
            return ch
        print(f"[WARN] conversations.open 실패: {j}")
        return raw
    return raw


CHANNEL_ID = resolve_channel_id(RAW_CHANNEL)


def send_text(ch: str, text: str) -> None:
    try:
        r = SESSION.post(f"{API}/chat.postMessage", data={"channel": ch, "text": text})
        j = r.json()
        if not j.get("ok"):
            print(f"[WARN] chat.postMessage 실패: {j}")
    except Exception as e:
        print(f"[WARN] chat.postMessage 예외: {e}")


def upload_external_form(p: Path, title: str, comment: Optional[str] = None) -> Tuple[bool, dict]:
    # 1) 업로드 URL 발급
    r1 = SESSION.post(
        f"{API}/files.getUploadURLExternal",
        data={"filename": p.name, "length": str(p.stat().st_size)},
    )
    try:
        j1 = r1.json()
    except Exception:
        return False, {
            "where": "getUploadURLExternal",
            "status": r1.status_code,
            "raw": r1.text[:300],
        }
    if not (r1.status_code == 200 and j1.get("ok")):
        return False, {"where": "getUploadURLExternal", **j1}

    url, fid = j1["upload_url"], j1["file_id"]

    # 2) PUT 업로드
    with open(p, "rb") as fp:
        put = requests.put(url, data=fp, headers={"Content-Type": _mime(p)})
    if not (200 <= put.status_code < 300):
        return False, {"where": "PUT", "status": put.status_code}

    # 3) 완료 호출
    files_field = json.dumps([{"id": fid, "title": title}], ensure_ascii=False)
    data = {"files": files_field, "channel_id": CHANNEL_ID}
    if comment:
        data["initial_comment"] = comment
    r3 = SESSION.post(f"{API}/files.completeUploadExternal", data=data)
    try:
        j3 = r3.json()
    except Exception:
        return False, {
            "where": "completeUploadExternal",
            "status": r3.status_code,
            "raw": r3.text[:300],
        }
    return (r3.status_code == 200 and j3.get("ok", False)), j3


def send_report(p: Path, title: str = "VELOS Report", comment: Optional[str] = None) -> bool:
    if not p.exists():
        print(f"[ERROR] 파일 없음: {p}")
        return False
    if not _ready(p):
        print(f"[ERROR] 파일 준비 안 됨(잠김/0바이트): {p}")
        return False
    ok, info = upload_external_form(p, title, comment)
    if ok:
        print(f"[OK] 업로드 성공: external(form) → {p}")
        send_text(CHANNEL_ID, f"VELOS 업로드 완료: {p.name}")
        return True
    print(f"[WARN] external(form) 실패: {info}")
    return False


def _find_latest() -> Optional[Path]:
    d = ROOT / "data" / "reports"
    if not d.exists():
        return None
    alias = d / "velos_report_latest.pdf"
    if alias.exists():
        return alias
    xs = sorted(d.glob("velos_report_*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
    return xs[0] if xs else None


if __name__ == "__main__":
    f = _find_latest()
    if not f:
        print("[WARN] 업로드할 파일 없음")
        sys.exit(0)
    print(f"[INFO] 업로드 대상: {f}")
    sys.exit(0 if send_report(f, title=f"VELOS Report - {f.name}") else 1)
