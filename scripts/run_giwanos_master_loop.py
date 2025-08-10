# -*- coding: utf-8 -*-
"""
VELOS 통합 마스터 루프 (Preflight·GPT‑5·ROOM 라우팅·안전 미러)
- .env: C:/giwanos/configs/.env
- 사전 점검(필수 키, Slack/Notion, 캐시·디스크, 룸 라우팅) 추가
- GPT‑5 규격 호출(엔진 내부에서 max_completion_tokens)
- 메모리 저장 + 선택 알림(Slack) + 선택 Notion 업로드
"""

from __future__ import annotations
import argparse, json, logging, os, sys, time, subprocess, re, locale, shutil
from pathlib import Path
from typing import Any, Optional

# ─ env
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="C:/giwanos/configs/.env")
except Exception:
    pass

BASE_DIR = Path("C:/giwanos")
sys.path.append(str(BASE_DIR))

# ─ 외부/코어 모듈
def _try_import(mod_path: str, attr: Optional[str] = None):
    try:
        m = __import__(mod_path, fromlist=[attr] if attr else [])
        return getattr(m, attr) if attr else m
    except Exception:
        return None

SlackClient = _try_import("modules.core.slack_client", "SlackClient")
upload_summary_to_notion = _try_import("tools.notion_integration.upload_summary_to_notion", "upload_summary_to_notion")

from modules.core.chat_rooms import base_room_id, sub_room_id, fresh_room
from modules.core.context_aware_decision_engine import generate_gpt_response_with_guard

# ─ 로깅
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "master_loop_execution.log"
logging.Formatter.converter = time.gmtime
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("velos.master")

# ─ 유틸
def _now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.utcnow().isoformat() + "Z"

def _run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    enc = locale.getpreferredencoding(False)
    p = subprocess.run(cmd, capture_output=True, text=True, encoding=enc, errors="replace", check=False)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()

def _find_field(text: Optional[str], label_patterns: list[str]) -> Optional[str]:
    if not text:
        return None
    for pat in label_patterns:
        m = re.search(pat + r"\s*:\s*(.+)", text)
        if m:
            v = m.group(1)
            return v.strip() if isinstance(v, str) else None
    return None

def _ntp_resync_and_log() -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        rc, out, _ = _run_cmd(["sc", "query", "w32time"])
        info["w32time_running"] = ("RUNNING" in (out or "").upper())

        rc2, _, err2 = _run_cmd(["w32tm", "/resync"])
        info["resync_rc"] = rc2
        if rc2 != 0:
            info["resync_error"] = (err2 or "access_denied_or_policy")[:200]

        rc_s, status, _ = _run_cmd(["w32tm", "/query", "/status"])
        info["status_rc"] = rc_s
        if status:
            info["stratum"] = _find_field(status, [r"\bStratum\b", r"\b계층\b"])
            info["precision"] = _find_field(status, [r"\bPrecision\b", r"\b정밀도\b"])
            info["last_sync"] = _find_field(status, [r"Last (Successful )?Sync Time", r"\b마지막으로 동기화한 시간\b"])
            info["poll_interval"] = _find_field(status, [r"\bPoll Interval\b", r"\b폴링 간격\b"])
            off = _find_field(status, [r"\bPhase Offset\b", r"\b위상 오프셋\b"])
            if off:
                m = re.search(r"([-\d\.]+)", off)
                info["offset"] = m.group(1) if m else off

        rc_p, peers, _ = _run_cmd(["w32tm", "/query", "/peers"])
        info["peers_rc"] = rc_p
        if peers:
            lines = [ln.strip() for ln in peers.splitlines() if ln.strip()]
            plist = []
            for ln in lines:
                if any(lbl in ln for lbl in ["Peer:", "피어:"]):
                    plist.append(ln.split(":", 1)[-1].strip())
            if plist:
                info["peer_list"] = plist

        rc_c, conf, _ = _run_cmd(["w32tm", "/query", "/configuration"])
        info["config_rc"] = rc_c
        if conf:
            info["type"] = _find_field(conf, [r"\bType:\b", r"\b형식:\b", r"\b유형:\b"])

        log.info(f"[ntp] {json.dumps({k:v for k,v in info.items() if not k.endswith('_raw')}, ensure_ascii=False)}")
    except Exception as e:
        info["error"] = str(e)
        log.warning(f"[ntp] 수집 실패: {e}")
    return info

def _env_snapshot() -> dict[str, Any]:
    keys = ["OPENAI_API_KEY", "OPENAI_MODEL", "SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID",
            "NOTION_TOKEN", "NOTION_ENABLED", "VELOS_NAMESPACE"]
    snap: dict[str, Any] = {}
    for k in keys:
        v = os.environ.get(k)
        snap[k] = (bool(v) if k not in ("OPENAI_MODEL", "VELOS_NAMESPACE") else (v or ""))
    return snap

# ─ 사전 점검
def _preflight(room_id: str) -> None:
    problems: list[str] = []
    warnings: list[str] = []

    # 필수 키
    for k in ["OPENAI_API_KEY", "OPENAI_MODEL"]:
        if not os.getenv(k):
            problems.append(f"필수 환경변수 누락: {k}")

    # Slack (선택)
    if os.getenv("SLACK_BOT_TOKEN") and not os.getenv("SLACK_CHANNEL_ID"):
        warnings.append("SLACK_BOT_TOKEN은 있는데 SLACK_CHANNEL_ID가 비어 있음")

    # Notion (선택)
    if os.getenv("NOTION_ENABLED", "0") == "1" and not os.getenv("NOTION_TOKEN"):
        problems.append("NOTION_ENABLED=1 이지만 NOTION_TOKEN 없음")

    # 캐시/디스크
    cache_root = os.getenv("HF_HOME") or os.getenv("TRANSFORMERS_CACHE") or "C:/giwanos/vector_cache"
    try:
        used, total = shutil.disk_usage(cache_root).used, shutil.disk_usage(cache_root).total
        free_gb = (total - used) / (1024**3)
        if free_gb < 1.0:
            warnings.append(f"모델/벡터 캐시 여유 공간 부족(<1GB): {cache_root}")
    except Exception:
        warnings.append(f"캐시 경로 확인 불가: {cache_root}")

    # 룸 라우팅 기본값
    if not room_id:
        warnings.append("ROOM 계산 실패(기본값 사용)")

    if problems:
        log.warning("[preflight] 차단급 이슈: " + "; ".join(problems))
    if warnings:
        log.info("[preflight] 경고: " + "; ".join(warnings))

# ─ 메모리 저장
DIALOG_MEMORY_PATH = BASE_DIR / "data" / "memory" / "dialog_memory.json"
DIALOG_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)

def save_dialog_memory(message: str, room_id: str):
    entry = {
        "session_id": time.strftime("%Y%m%d_%H%M%S"),
        "created_at": _now_iso(),
        "room_id": room_id,
        "conversations": [{"role": "system", "message": message, "timestamp": _now_iso()}],
    }
    try:
        if DIALOG_MEMORY_PATH.exists():
            try:
                blob = json.loads(DIALOG_MEMORY_PATH.read_text(encoding="utf-8"))
            except Exception:
                blob = {"sessions": []}
        else:
            blob = {"sessions": []}
        blob.setdefault("sessions", []).append(entry)
        DIALOG_MEMORY_PATH.write_text(json.dumps(blob, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("✅ 메모리 저장 완료")
    except Exception as e:
        log.warning(f"[memory] 저장 실패: {e}")

# ─ 알림
def _notify_slack(text: str, channel_env: str = "SLACK_CHANNEL_ID") -> bool:
    if SlackClient is None:
        return False
    try:
        ch = os.environ.get(channel_env) or "#summary"
        SlackClient().send_message(ch, text)
        return True
    except Exception as e:
        log.warning(f"[slack] 실패: {e}")
        return False

def _upload_notion_summary(summary_path: str) -> bool:
    if os.environ.get("NOTION_ENABLED", "0") != "1":
        return False
    if upload_summary_to_notion is None:
        log.warning("[notion] 모듈 없음")
        return False
    try:
        # summary_path 키워드/위치 인수 혼용 지원
        try:
            upload_summary_to_notion(summary_path=summary_path)  # type: ignore
        except TypeError:
            upload_summary_to_notion(summary_path)  # type: ignore
        return True
    except Exception as e:
        log.warning(f"[notion] 업로드 실패: {e}")
        return False

# ─ 인자
def _args():
    p = argparse.ArgumentParser()
    p.add_argument("--check-only", action="store_true", help="점검 모드: 외부 전송 최소화")
    p.add_argument("--weekly", action="store_true", help="주간 보고 모드")
    p.add_argument("--verbose", action="store_true", help="자세한 로깅")
    p.add_argument("--project", type=str, default=os.getenv("ROUTE_PROJECT") or None)
    p.add_argument("--topic", type=str, default=os.getenv("ROUTE_TOPIC") or None)
    p.add_argument("--fresh", action="store_true", default=(os.getenv("ROOM_FRESH", "0") == "1"))
    return p.parse_args()

# ─ 메인
def main():
    args = _args()
    if args.verbose:
        log.setLevel(logging.DEBUG)

    # 룸 라우팅
    room = base_room_id()
    if args.fresh:
        room = fresh_room()
    elif args.project or args.topic:
        room = sub_room_id(args.project, args.topic)

    # 사전 점검
    _preflight(room)

    # 스냅샷
    ntp = _ntp_resync_and_log()
    envs = _env_snapshot()

    # 요약 (ChatSyncGuard 경유)
    summary = ""
    try:
        prompt = (
            f"[room={room}] 다음 NTP/환경 상태를 한 줄로 요약하고, 이상이 있으면 짧게 지적해줘.\n"
            f"NTP={json.dumps(ntp, ensure_ascii=False)[:600]}\n"
            f"ENV={json.dumps(envs, ensure_ascii=False)[:400]}"
        )
        summary = generate_gpt_response_with_guard(prompt, conversation_id=room)
        log.info(f"[summary room={room}] {summary}")
        if summary:
            save_dialog_memory(summary, room_id=room)
    except Exception as e:
        log.warning(f"[summary] 실패: {e}")

    # 전송(선택)
    try:
        if not args.check_only:
            _notify_slack("✅ VELOS 루프 완료")
            summary_file = str(BASE_DIR / "data" / "reports" / "summary_dashboard.json")
            if Path(summary_file).exists():
                _upload_notion_summary(summary_file)
    except Exception as e:
        log.warning(f"[notify] 실패: {e}")

    if args.weekly:
        log.info("[weekly] 주간 보고 모드 실행 완료(구현 모듈 연계 지점)")

if __name__ == "__main__":
    main()
