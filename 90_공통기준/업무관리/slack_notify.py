"""
slack_notify.py — Phase 4 Slack 알림 엔진
- STATUS/TASKS 갱신 결과, Git 커밋 결과, 핵심 파일 변경 시 알림
- batch_id 기반 중복 발송 방지
- Bot Token: 환경변수 SLACK_BOT_TOKEN 또는 .env 파일에서 로드
"""

import fnmatch
import json
import logging
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import yaml

# ── 설정 로드 ──────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "slack_config.yaml"
DEDUP_STATE_PATH = Path(__file__).parent / ".slack_dedup_state.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 토큰 로드 ─────────────────────────────────────────────────────────────

def load_token(cfg: dict) -> str:
    """환경변수 → .env 파일 순서로 토큰 로드."""
    env_key = cfg["slack"].get("token_env", "SLACK_BOT_TOKEN")

    # 1. 환경변수 확인
    token = os.environ.get(env_key, "")
    if token.startswith("xoxb-") or token.startswith("xoxp-"):
        return token

    # 2. .env 파일 fallback
    fallback_path = cfg["slack"].get("token_env_fallback_path", "")
    if fallback_path:
        env_file = Path(fallback_path)
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith(env_key + "="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val.startswith("xoxb-") or val.startswith("xoxp-"):
                        return val

    return ""


# ── 에러 로거 ─────────────────────────────────────────────────────────────

def setup_error_logger(cfg: dict) -> logging.Logger:
    repo_root = Path(__file__).parent.parent.parent  # 업무리스트 루트 추정
    log_dir = cfg.get("logging", {}).get("log_dir", "90_공통기준/업무관리")
    prefix = cfg.get("logging", {}).get("error_prefix", "slack_errors_")
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = repo_root / log_dir / f"{prefix}{date_str}.log"

    logger = logging.getLogger("slack_errors")
    if not logger.handlers:
        logger.setLevel(logging.ERROR)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        h = logging.FileHandler(log_path, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(h)
    return logger


# ── 중복 방지 ─────────────────────────────────────────────────────────────

def _load_dedup_state() -> dict:
    if DEDUP_STATE_PATH.exists():
        try:
            return json.loads(DEDUP_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_dedup_state(state: dict):
    try:
        DEDUP_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _is_duplicate(batch_id: str, dedup_hours: int) -> bool:
    state = _load_dedup_state()
    if batch_id not in state:
        return False
    ts = state[batch_id]
    cutoff = (datetime.now() - timedelta(hours=dedup_hours)).isoformat()
    return ts > cutoff


def _mark_sent(batch_id: str, dedup_hours: int):
    state = _load_dedup_state()
    state[batch_id] = datetime.now().isoformat()
    # 오래된 항목 정리
    cutoff = (datetime.now() - timedelta(hours=dedup_hours * 2)).isoformat()
    state = {k: v for k, v in state.items() if v > cutoff}
    _save_dedup_state(state)


# ── Slack API ─────────────────────────────────────────────────────────────

def _slack_post(token: str, channel_id: str, text: str,
                retry_count: int, retry_delay: int,
                logger: logging.Logger) -> bool:
    """chat.postMessage API 호출."""
    url = "https://slack.com/api/chat.postMessage"
    payload = json.dumps({
        "channel": channel_id,
        "text": text,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {token}",
    }

    for attempt in range(retry_count + 1):
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if body.get("ok"):
                    return True
                error = body.get("error", "unknown")
                logger.error(f"Slack API 오류: {error}")
                return False
        except Exception as e:
            if attempt < retry_count:
                time.sleep(retry_delay)
            else:
                logger.error(f"Slack 발송 실패 (시도 {attempt+1}): {e}")
    return False


# ── 메시지 조립 ───────────────────────────────────────────────────────────

def _has_critical(events: list, critical_patterns: list) -> list:
    """배치 이벤트 중 핵심 파일 해당 항목 반환."""
    hits = []
    for abs_path, entry in events:
        fname = Path(abs_path).name
        if any(fnmatch.fnmatch(fname, p) for p in critical_patterns):
            hits.append(fname)
    return hits


def build_message(
    batch_id: str,
    events: list,
    phase3_result: dict,   # {"ok": bool, "modified": list}
    phase2_result: dict,   # {"committed": int, "failed": int, "commit_sha": str}
    critical_patterns: list,
    notify_cfg: dict,
) -> str | None:
    """
    알림 발송 여부 판단 및 메시지 조립.
    발송 불필요 시 None 반환.
    """
    lines = []
    should_notify = False

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_count = len(events)

    # 핵심 파일 변경 감지
    if notify_cfg.get("critical_file_changed", True):
        critical_hits = _has_critical(events, critical_patterns)
        if critical_hits:
            should_notify = True
            lines.append(f"[핵심 파일 변경] {', '.join(critical_hits)}")

    # Phase 3 결과
    if phase3_result:
        if phase3_result.get("ok") and phase3_result.get("modified"):
            if notify_cfg.get("status_tasks_updated", True):
                should_notify = True
                updated = ", ".join(Path(p).name for p in phase3_result["modified"])
                lines.append(f"[STATUS/TASKS 갱신] {updated}")
        elif not phase3_result.get("ok") and notify_cfg.get("status_tasks_failed", True):
            should_notify = True
            lines.append("[STATUS/TASKS 갱신 실패]")

    # Phase 2 결과
    if phase2_result:
        committed = phase2_result.get("committed", 0)
        failed = phase2_result.get("failed", 0)
        sha = phase2_result.get("commit_sha", "")

        if committed > 0 and notify_cfg.get("git_commit_success", True):
            should_notify = True
            sha_short = sha[:7] if sha else "-"
            lines.append(f"[Git 커밋] {committed}건 커밋 ({sha_short})")
        if failed > 0 and notify_cfg.get("git_commit_failed", True):
            should_notify = True
            lines.append(f"[Git 커밋 실패] {failed}건")

    if not should_notify:
        return None

    header = f"*업무리스트 AutoBot* | {ts} | 배치 {batch_id[:8]}"
    summary = f"파일 {file_count}건 처리"
    body = "\n".join(lines)

    return f"{header}\n{summary}\n{body}"


# ── 핵심: 알림 발송 ───────────────────────────────────────────────────────

def notify_batch(
    batch_id: str,
    events: list,
    phase3_result: dict = None,
    phase2_result: dict = None,
    cfg: dict = None,
    dry_run: bool = False,
    logger: logging.Logger = None,
) -> bool:
    """
    배치 완료 후 Slack 알림 발송.
    반환: True(발송 성공 또는 발송 불필요), False(발송 실패)
    """
    if cfg is None:
        cfg = load_config()
    if logger is None:
        logger = setup_error_logger(cfg)

    slack_cfg = cfg.get("slack", {})
    notify_cfg = slack_cfg.get("notify_on", {})
    critical_patterns = slack_cfg.get("critical_patterns", [])
    dedup_hours = slack_cfg.get("dedup_window_hours", 1)
    channel_id = slack_cfg.get("channel_id", "")
    retry_count = slack_cfg.get("retry_count", 2)
    retry_delay = slack_cfg.get("retry_delay_seconds", 3)

    # 중복 방지
    if _is_duplicate(batch_id, dedup_hours):
        return True

    # 메시지 조립
    msg = build_message(
        batch_id=batch_id,
        events=events,
        phase3_result=phase3_result or {},
        phase2_result=phase2_result or {},
        critical_patterns=critical_patterns,
        notify_cfg=notify_cfg,
    )

    if msg is None:
        return True  # 발송 불필요

    if dry_run:
        print(f"[DRY-RUN SLACK]\n{msg}")
        return True

    # 토큰 로드
    token = load_token(cfg)
    if not token:
        logger.error("Slack 토큰 없음 — SLACK_BOT_TOKEN 환경변수 또는 .env 파일 확인")
        return False

    ok = _slack_post(token, channel_id, msg, retry_count, retry_delay, logger)
    if ok:
        _mark_sent(batch_id, dedup_hours)
    return ok


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4 Slack 알림 테스트")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-id", default="test1234")
    parser.add_argument("--message", default="")
    args = parser.parse_args()

    cfg = load_config()
    logger = setup_error_logger(cfg)

    if args.message:
        # 직접 메시지 발송
        if args.dry_run:
            print(f"[DRY-RUN SLACK]\n{args.message}")
            return
        token = load_token(cfg)
        if not token:
            print("토큰 없음")
            return
        ok = _slack_post(
            token,
            cfg["slack"]["channel_id"],
            args.message,
            cfg["slack"].get("retry_count", 2),
            cfg["slack"].get("retry_delay_seconds", 3),
            logger,
        )
        print("발송 성공" if ok else "발송 실패")
        return

    # 테스트 배치 알림
    test_events = [
        ("C:/Users/User/Desktop/업무리스트/CLAUDE.md",
         {"event_type": "modified"}),
        ("C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/test.skill",
         {"event_type": "created"}),
    ]
    test_phase3 = {"ok": True, "modified": ["STATUS.md", "TASKS.md"]}
    test_phase2 = {"committed": 2, "failed": 0, "commit_sha": "abc1234def"}

    ok = notify_batch(
        batch_id=args.batch_id,
        events=test_events,
        phase3_result=test_phase3,
        phase2_result=test_phase2,
        cfg=cfg,
        dry_run=args.dry_run,
        logger=logger,
    )
    print("알림 발송 성공" if ok else "알림 발송 실패")


if __name__ == "__main__":
    main()
