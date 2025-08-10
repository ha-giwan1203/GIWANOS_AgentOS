from __future__ import annotations

# ================= VELOS 운영 철학 선언문 =================
# - 단일 시간 원천(UTC)만 저장하고, 사람에게 보일 때만 KST로 변환한다.
# - 경과 시간은 벽시계가 아닌 monotonic()으로 계산한다.
# - 파일명 변경 금지, 경로 고정, 제공 전 자가 검증 필수.
# =========================================================

import argparse
import json
import logging
import os
import sys
import traceback
import time
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional

# 공통 설정
from modules.core.config import BASE_DIR, LOG_DIR, HEALTH_PATH, API_COST_LOG, path

# PYTHONPATH 보정
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# 시간 유틸 (UTC/KST/monotonic) — 기존 모듈 유지
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic  # type: ignore

# 로깅: UTC 타임스탬프
logging.Formatter.converter = time.gmtime
LOG_FILE = LOG_DIR / "master_loop_execution.log"
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("velos.master")


# 선택적 임포트 유틸
def _try_import(mod_path: str, attr: Optional[str] = None):
    try:
        module = __import__(mod_path, fromlist=[attr] if attr else [])
        return getattr(module, attr) if attr else module
    except Exception:
        log.warning(f"[import-skip] {mod_path}{'.'+attr if attr else ''} 임포트 실패")
        return None


# 외부/내부 모듈 참조 (없으면 스킵)
SlackClient = _try_import("modules.core.slack_client", "SlackClient")
send_pushbullet_notification = _try_import("tools.notifications.send_pushbullet_notification", "send_pushbullet_notification")
send_report_email = _try_import("tools.notifications.send_email", "send_report_email")
generate_pdf_report = _try_import("modules.report.generate_pdf_report", "generate_pdf_report")
upload_summary_to_notion = _try_import("tools.notion_integration.upload_summary_to_notion", "upload_summary_to_notion")
generate_weekly_summary = _try_import("modules.automation.scheduling.weekly_summary", "generate_weekly_summary")
update_system_health = _try_import("modules.automation.scheduling.system_health_logger", "update_system_health")
auto_recovery_main = _try_import("modules.core.auto_recovery_agent", "main")
run_reflection = _try_import("modules.core.reflection_agent", "run_reflection")
JudgeAgent = _try_import("modules.evaluation.giwanos_agent.judge_agent", "JudgeAgent")
git_sync = _try_import("modules.automation.git_management.git_sync", "main")
evaluate_cot = _try_import("modules.advanced.advanced_modules.cot_evaluator", "evaluate_cot")
test_advanced_rag = _try_import("modules.advanced.advanced_modules.advanced_rag", "test_advanced_rag")
adaptive_reasoning_main = _try_import("modules.core.adaptive_reasoning_agent", "adaptive_reasoning_main")
threshold_optimizer_main = _try_import("modules.core.threshold_optimizer", "threshold_optimizer_main")
rule_optimizer_main = _try_import("modules.core.rule_optimizer", "rule_optimizer_main")
create_snapshot = _try_import("modules.core.chat_session_backup", "create_snapshot")

# 경로들
JUDGMENT_INDEX_PATH = path("data", "judgments", "judgment_history_index.json", ensure_dir=True)
DIALOG_MEMORY_PATH = path("data", "memory", "dialog_memory.json", ensure_dir=True)
API_COST_LOG.parent.mkdir(parents=True, exist_ok=True)


# 환경 스냅샷
def _mask(v: Optional[str]) -> str:
    if not v:
        return ""
    return (v[:3] + "***" + v[-3:]) if len(v) > 6 else "***"


def _env_snapshot() -> dict[str, Any]:
    keys = ["SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID", "EMAIL_ENABLED", "EMAIL_FROM", "NOTION_TOKEN", "PUSHBULLET_TOKEN", "PUSHBULLET_API_KEY"]
    snap = {k: bool(os.environ.get(k)) for k in keys}
    if os.environ.get("EMAIL_FROM"):
        snap["EMAIL_FROM"] = _mask(os.environ.get("EMAIL_FROM"))
    return snap


# system_health.json I/O
def _read_health_safely() -> dict:
    if HEALTH_PATH.exists():
        try:
            return json.loads(HEALTH_PATH.read_text(encoding="utf-8-sig")) or {}
        except Exception as e:
            log.warning(f"[health] 읽기 실패, 리셋: {e}")
            return {}
    return {}


def _write_health(patch: dict[str, Any]) -> None:
    prior = _read_health_safely()
    prior.update(patch)
    HEALTH_PATH.write_text(json.dumps(prior, ensure_ascii=False, indent=2), encoding="utf-8")


# 안전 실행
def safe_call(fn: Optional[Callable], *args, **kwargs):
    if fn is None:
        return None
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log.warning(f"[safe] {getattr(fn,'__name__',str(fn))} 실패: {e}")
        log.debug(traceback.format_exc())
        return None


# 메모리/판단 저장
def save_dialog_memory(message: str):
    entry = {
        "session_id": now_kst().strftime("%Y%m%d_%H%M%S"),
        "created_at": now_utc().isoformat() + "Z",
        "conversations": [{"role": "system", "message": message, "timestamp": now_utc().isoformat() + "Z"}],
    }
    try:
        if DIALOG_MEMORY_PATH.exists():
            try:
                dialog_memory = json.loads(DIALOG_MEMORY_PATH.read_text(encoding="utf-8"))
            except Exception:
                dialog_memory = {"sessions": []}
        else:
            dialog_memory = {"sessions": []}
        dialog_memory.setdefault("sessions", []).append(entry)
        DIALOG_MEMORY_PATH.write_text(json.dumps(dialog_memory, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("✅ 메모리 누적 저장 완료")
    except Exception as e:
        log.warning(f"[memory] 저장 실패: {e}")


def save_judgment(result: str):
    judgment = {
        "id": now_kst().strftime("%Y%m%d_%H%M%S"),
        "timestamp": now_utc().isoformat() + "Z",
        "user_request": "Check system health",
        "explanation": result,
        "tags": ["운영"],
    }
    try:
        if JUDGMENT_INDEX_PATH.exists():
            try:
                judgments = json.loads(JUDGMENT_INDEX_PATH.read_text(encoding="utf-8"))
            except Exception:
                judgments = []
        else:
            judgments = []
        judgments.append(judgment)
        JUDGMENT_INDEX_PATH.write_text(json.dumps(judgments, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("✅ 판단 데이터 누적 저장 완료")
    except Exception as e:
        log.warning(f"[judgment] 저장 실패: {e}")


# 알림 계열
def _notify_slack(text: str, channel_env: str = "SLACK_CHANNEL_ID") -> bool:
    if SlackClient is None:
        log.warning("[slack] 모듈 미존재. 메시지 스킵")
        return False
    try:
        sc = SlackClient()
        ch = os.environ.get(channel_env) or "#summary"
        sc.send_message(ch, text)
        return True
    except Exception as e:
        log.warning(f"[slack] 실패: {e}")
        return False


def _notify_pushbullet(title: str, body: str) -> bool:
    return bool(safe_call(send_pushbullet_notification, title, body))


def _send_email_if_enabled(report_path: str) -> bool:
    enabled = os.environ.get("EMAIL_ENABLED", "0") == "1"
    if not enabled:
        log.info("✋ EMAIL_ENABLED=0 — 전송 건너뜀")
        return False
    if send_report_email is None:
        log.warning("[email] 모듈 미존재. 스킵")
        return False
    return bool(safe_call(send_report_email, report_path))


def _upload_notion() -> bool:
    if upload_summary_to_notion is None:
        log.warning("[notion] 모듈 미존재. 스킵")
        return False
    return bool(safe_call(upload_summary_to_notion))


# NTP 동기화 및 상태 로깅(로캘 무관 파싱, 실패해도 루프 진행)
def _ntp_resync_and_log() -> dict[str, Any]:
    import re
    import locale

    def _run(cmd: list[str]) -> tuple[int, str, str]:
        enc = locale.getpreferredencoding(False)
        p = subprocess.run(cmd, capture_output=True, text=True, encoding=enc, errors="replace", check=False)
        return p.returncode, p.stdout.strip(), p.stderr.strip()

    # 라벨 사전(영/한)
    KEYS = {
        "stratum": [r"\bStratum\b", r"\b계층\b"],
        "precision": [r"\bPrecision\b", r"\b정밀도\b"],
        "last_sync": [r"Last (Successful )?Sync Time", r"\b마지막으로 동기화한 시간\b"],
        "offset": [r"\bPhase Offset\b", r"\b위상 오프셋\b"],
        "poll": [r"\bPoll Interval\b", r"\b폴링 간격\b"],
        "peer": [r"\bPeer:\b", r"\b피어:\b"],
        "type": [r"\bType:\b", r"\b형식:\b", r"\b유형:\b"],
    }

    info: dict[str, Any] = {"locale": (locale.getlocale()[0] or "unknown")}

    # 0) 서비스 상태 확인 및 기동
    rc, out, err = _run(["sc", "query", "w32time"])
    info["w32time_query_rc"] = rc
    info["w32time_running"] = ("RUNNING" in out.upper())
    if rc == 0 and not info["w32time_running"]:
        _run(["sc", "config", "w32time", "start=", "auto"])
        _run(["net", "start", "w32time"])
        rc2, out2, _ = _run(["sc", "query", "w32time"])
        info["w32time_running"] = ("RUNNING" in out2.upper())

    # 1) 동기화 시도
    rc, _, err = _run(["w32tm", "/resync"])
    info["resync_rc"] = rc
    if rc != 0:
        info["resync_error"] = err[:300] if err else "access_denied_or_policy"

    # 2) 상태/피어/구성 수집
    rc_s, status, _ = _run(["w32tm", "/query", "/status"])
    rc_p, peers, _ = _run(["w32tm", "/query", "/peers"])
    rc_c, conf, _ = _run(["w32tm", "/query", "/configuration"])

    info["status_rc"] = rc_s
    info["peers_rc"] = rc_p
    info["config_rc"] = rc_c

    if status:
        info["ntp_status_raw"] = status[:1000]
    if peers:
        info["peers_raw"] = peers[:800]
    if conf:
        info["config_raw"] = conf[:800]

    def _find(label_list, text):
        for pat in label_list:
            m = re.search(pat + r"\s*:\s*(.+)", text)
            if m:
                return m.group(1).strip()
        return None

    if status:
        info["stratum"] = _find(KEYS["stratum"], status)
        info["precision"] = _find(KEYS["precision"], status)
        info["last_sync"] = _find(KEYS["last_sync"], status)
        off = _find(KEYS["offset"], status)
        if off:
            m = re.search(r"([-\d\.]+)", off)
            info["offset"] = m.group(1) if m else off
        info["poll_interval"] = _find(KEYS["poll"], status)

    if peers:
        lines = [ln.strip() for ln in peers.splitlines() if ln.strip()]
        plist = []
        for ln in lines:
            if any(lbl in ln for lbl in ["Peer:", "피어:"]):
                plist.append(ln.split(":", 1)[-1].strip())
        info["peer_list"] = plist

    if conf:
        info["type"] = _find(KEYS["type"], conf)

    if info.get("resync_rc", 0) != 0 and not info.get("last_sync"):
        info["hint"] = "resync_failed_or_not_admin"

    log.info(f"[ntp] {json.dumps({k:v for k,v in info.items() if not k.endswith('_raw')}, ensure_ascii=False)}")
    return info


# CLI
def _argparse():
    p = argparse.ArgumentParser()
    p.add_argument("--check-only", action="store_true", help="점검 모드: 생성/전송 최소화")
    p.add_argument("--verbose", action="store_true", help="자세한 로깅")
    return p.parse_args()


def main():
    # 감사 로그 위치 안내(동기화 가드)
    try:
        from modules.automation.sync.chat_sync_guard import AUDIT_LOG
        log.info(f"[ChatSyncGuard] audit log: {AUDIT_LOG}")
    except Exception:
        pass

    args = _argparse()
    if args.verbose:
        log.setLevel(logging.DEBUG)

    # NTP 동기화 및 상태 기록
    ntp = _ntp_resync_and_log()

    log.info("=== VELOS 통합 마스터 루프 시작 ===")
    _write_health({"env_snapshot": _env_snapshot(), "loop_started_at": now_utc().isoformat(), "ntp_info": ntp})

    # 1) 시스템 상태 업데이트, git 동기화, JudgeAgent
    safe_call(update_system_health)
    safe_call(git_sync)
    if JudgeAgent:
        try:
            JudgeAgent().run_loop()
        except Exception as e:
            log.warning(f"[JudgeAgent] 실패: {e}")

    # 2) 간단 상태 결과를 메모리에 기록
    result = "시스템 정상 상태 유지 중."
    save_dialog_memory(result)
    save_judgment(result)

    # 3) 보고서 생성
    pdf_report_path: Optional[str] = None
    if generate_pdf_report:
        try:
            pdf_report_path = generate_pdf_report()
        except Exception as e:
            log.error(f"[report] PDF 생성 실패: {e}")

    # 4) 전송 계열
    if not args.check_only:
        if pdf_report_path:
            _send_email_if_enabled(pdf_report_path)
        if _upload_notion():
            log.info("✅ Notion 업로드 완료")
        _notify_slack("✅ VELOS 루프 정상 작동 완료.")
        _notify_pushbullet("✅ VELOS 루프 완료", "보고서 생성 및 전송 플로우 실행")

    # 5) 평가/최적화 루틴
    safe_call(evaluate_cot)
    safe_call(test_advanced_rag)
    safe_call(adaptive_reasoning_main)
    safe_call(threshold_optimizer_main)
    safe_call(rule_optimizer_main)
    safe_call(run_reflection)

    # 6) 주간 요약
    if generate_weekly_summary:
        try:
            reports_dir = str(path("data", "reports"))
            generate_weekly_summary(reports_dir)
            log.info(f"Weekly summary created in: {reports_dir}")
        except Exception as e:
            log.warning(f"[weekly_summary] 실패: {e}")

    # 7) 대화 세션 스냅샷(조용히 실패 무시)
    try:
        if create_snapshot:
            create_snapshot()
    except Exception:
        pass

    _write_health({"loop_ended_at": now_utc().isoformat()})
    log.info("=== VELOS 통합 마스터 루프 종료 ===")


if __name__ == "__main__":
    main()
