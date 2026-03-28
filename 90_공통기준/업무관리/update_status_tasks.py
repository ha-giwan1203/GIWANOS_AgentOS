"""
update_status_tasks.py — STATUS.md / TASKS.md 자동 갱신 엔진 (Phase 3)
- Phase 1 flush 이벤트에서 운영 의미 있는 변경만 추려 STATUS.md에 이력 추가
- 규칙에 따라 TASKS.md에 [auto] 후속작업 추가
- STATUS/TASKS 자체 변경은 무한루프 방지를 위해 제외
- 실패 시 원본 파일 보존, 오류 로그만 기록
"""

import json
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import yaml

# ── 설정 로드 ──────────────────────────────────────────────────────────────

RULES_PATH = Path(__file__).parent / "status_rules.yaml"
STATUS_PATH = Path(__file__).parent / "STATUS.md"
TASKS_PATH  = Path(__file__).parent / "TASKS.md"
ERROR_LOG_DIR = Path(__file__).parent


def load_rules(path: Path = RULES_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 에러 로거 ─────────────────────────────────────────────────────────────

def setup_error_logger() -> logging.Logger:
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = ERROR_LOG_DIR / f"status_tasks_errors_{date_str}.log"
    logger = logging.getLogger("status_tasks_errors")
    if not logger.handlers:
        logger.setLevel(logging.ERROR)
        h = logging.FileHandler(log_path, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(h)
    return logger


# ── 패턴 매칭 ─────────────────────────────────────────────────────────────

def _matches(rel_path: str, pattern: str) -> bool:
    try:
        return Path(rel_path).match(pattern) or Path(Path(rel_path).name).match(pattern)
    except Exception:
        return False


def _matches_any(rel_path: str, patterns: list) -> bool:
    return any(_matches(rel_path, p) for p in patterns)


def classify_event(abs_path: str, repo_root: str, rules: dict) -> dict | None:
    """
    이벤트가 운영 의미 있는지 판단.
    반환: {"label": str, "add_task": bool, "task_text": str} 또는 None(제외 대상)
    """
    try:
        rel = Path(os.path.relpath(abs_path, repo_root)).as_posix()
    except ValueError:
        return None

    skip_patterns = rules.get("skip", [])
    if _matches_any(rel, skip_patterns):
        return None

    for rule in rules.get("meaningful", []):
        if _matches(rel, rule["pattern"]):
            if rule.get("label") is None:
                return None
            return {
                "label": rule["label"],
                "add_task": rule.get("add_task", False),
                "task_text": rule.get("task_text", ""),
            }
    return None


# ── 안전 파일 쓰기 (원본 보존) ────────────────────────────────────────────

def safe_write(target: Path, new_content: str, logger: logging.Logger) -> bool:
    """임시 파일에 먼저 쓰고 성공 시 rename. 실패해도 원본 유지."""
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=target.parent, suffix=".tmp", prefix=target.stem + "_"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(new_content)
            shutil.move(tmp_path, str(target))
            return True
        except Exception as e:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            logger.error(f"safe_write 실패: {e} | {target}")
            return False
    except Exception as e:
        logger.error(f"safe_write 임시파일 생성 실패: {e}")
        return False


# ── STATUS.md 갱신 ────────────────────────────────────────────────────────

SECTION_MARKER = "## 자동 감지 변경 이력"
ENTRY_PREFIX   = "| "


def _build_status_entry(timestamp: str, label: str, file_name: str, event_type: str) -> str:
    return f"| {timestamp} | {event_type:8s} | {file_name} | {label} |"


def update_status_md(
    entries: list,          # [{"timestamp": str, "label": str, "file_name": str, "event_type": str}]
    max_entries: int,
    dry_run: bool,
    logger: logging.Logger,
) -> bool:
    if not STATUS_PATH.exists():
        logger.error(f"STATUS.md 없음: {STATUS_PATH}")
        return False
    if not entries:
        return True

    content = STATUS_PATH.read_text(encoding="utf-8")

    # 섹션 존재 여부 확인
    if SECTION_MARKER in content:
        # 기존 섹션 파싱
        before, _, after = content.partition(SECTION_MARKER)
        # 기존 항목 추출
        existing_lines = []
        header_done = False
        for line in after.splitlines():
            if not header_done:
                if line.startswith("|---"):
                    header_done = True
                continue
            if line.startswith(ENTRY_PREFIX):
                existing_lines.append(line)
    else:
        before = content.rstrip() + "\n\n"
        existing_lines = []

    # 신규 항목 생성 (최신 순)
    new_lines = [
        _build_status_entry(e["timestamp"], e["label"], e["file_name"], e["event_type"])
        for e in reversed(entries)
    ]

    # 병합 후 max_entries 유지
    all_lines = new_lines + existing_lines
    all_lines = all_lines[:max_entries]

    table_header = (
        f"\n| 시각 | 이벤트 | 파일 | 변경 내용 |\n"
        f"|------|--------|------|----------|\n"
    )
    section_content = SECTION_MARKER + table_header + "\n".join(all_lines) + "\n"

    new_content = before.rstrip("\n") + "\n\n" + section_content

    if dry_run:
        for line in new_lines:
            print(f"[DRY-RUN STATUS] {line}")
        return True

    return safe_write(STATUS_PATH, new_content, logger)


# ── TASKS.md 갱신 ─────────────────────────────────────────────────────────

def _already_has_task(content: str, task_text: str, window_hours: int) -> bool:
    """최근 window_hours 이내에 동일 [auto] 작업이 이미 있는지 확인."""
    pattern = re.compile(
        r"\[auto\].*?" + re.escape(task_text), re.IGNORECASE
    )
    return bool(pattern.search(content))


def update_tasks_md(
    task_items: list,       # [{"task_text": str, "source_file": str}]
    dedup_window_hours: int,
    auto_tag: str,
    dry_run: bool,
    logger: logging.Logger,
) -> bool:
    if not TASKS_PATH.exists():
        logger.error(f"TASKS.md 없음: {TASKS_PATH}")
        return False

    new_tasks = [t for t in task_items if t.get("task_text")]
    if not new_tasks:
        return True

    content = TASKS_PATH.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # 중복 제거
    to_add = []
    for item in new_tasks:
        if not _already_has_task(content, item["task_text"], dedup_window_hours):
            to_add.append(item)

    if not to_add:
        return True

    pending_header = "## 대기 중 (우선순위 순)"
    if pending_header not in content:
        # 섹션 없으면 파일 끝에 추가
        insert_pos = len(content)
        prefix = content.rstrip() + f"\n\n{pending_header}\n\n"
        suffix = ""
    else:
        idx = content.index(pending_header) + len(pending_header)
        prefix = content[:idx]
        suffix = content[idx:]
        insert_pos = None

    new_lines = []
    for item in to_add:
        src = Path(item["source_file"]).name
        new_lines.append(
            f"\n### {auto_tag} {item['task_text']} ({today})\n"
            f"- 출처: `{src}` 변경 감지\n"
            f"- 자동 생성 항목 — 확인 후 처리 또는 삭제\n"
        )

    if insert_pos is None:
        new_content = prefix + "\n".join(new_lines) + "\n" + suffix
    else:
        new_content = prefix + "\n".join(new_lines) + suffix

    if dry_run:
        for item in to_add:
            print(f"[DRY-RUN TASKS] [auto] {item['task_text']}")
        return True

    return safe_write(TASKS_PATH, new_content, logger)


# ── 핵심: 이벤트 처리 ─────────────────────────────────────────────────────

def process_events(
    events: list,           # [(abs_path, entry_dict), ...]
    repo_root: str,
    rules: dict = None,
    dry_run: bool = False,
    logger: logging.Logger = None,
) -> list:
    """
    Phase 1 flush 이벤트를 받아 STATUS.md / TASKS.md 갱신.
    반환: 갱신된 파일 abs_path 목록 (Phase 2에 전달용)
    """
    if logger is None:
        logger = setup_error_logger()
    if rules is None:
        rules = load_rules()

    cfg_status = rules.get("status", {})
    cfg_tasks  = rules.get("tasks", {})
    max_entries = cfg_status.get("max_entries", 30)
    date_fmt    = cfg_status.get("date_format", "%Y-%m-%d %H:%M")
    dedup_hours = cfg_tasks.get("dedup_window_hours", 24)
    auto_tag    = cfg_tasks.get("auto_tag", "[auto]")

    status_entries = []
    task_items     = []

    for abs_path, entry in events:
        event_type = entry.get("event_type", "modified")
        if event_type == "deleted":
            continue

        info = classify_event(abs_path, repo_root, rules)
        if info is None:
            continue

        ts = datetime.now().strftime(date_fmt)
        status_entries.append({
            "timestamp": ts,
            "label": info["label"],
            "file_name": Path(abs_path).name,
            "event_type": event_type,
        })

        if info["add_task"] and info.get("task_text"):
            task_items.append({
                "task_text": info["task_text"],
                "source_file": abs_path,
            })

    modified_files = []

    if status_entries:
        ok = update_status_md(status_entries, max_entries, dry_run, logger)
        if ok and not dry_run:
            modified_files.append(str(STATUS_PATH))

    if task_items:
        ok = update_tasks_md(task_items, dedup_hours, auto_tag, dry_run, logger)
        if ok and not dry_run:
            if str(TASKS_PATH) not in modified_files:
                modified_files.append(str(TASKS_PATH))

    return modified_files


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="STATUS.md / TASKS.md 자동 갱신")
    parser.add_argument("--rules", default=str(RULES_PATH))
    parser.add_argument("--repo-root",
                        default="C:/Users/User/Desktop/업무리스트")
    parser.add_argument("--log-file", help="처리할 JSONL 작업로그 파일")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger = setup_error_logger()
    rules  = load_rules(Path(args.rules))

    if args.log_file:
        log_path = Path(args.log_file)
    else:
        from datetime import datetime as _dt
        date_str = _dt.now().strftime("%Y%m%d")
        log_path = Path(args.repo_root) / "90_공통기준/업무관리" / f"작업로그_{date_str}.jsonl"

    if not log_path.exists():
        print(f"로그 파일 없음: {log_path}")
        return

    events = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                abs_path = rec.get("file_path", "").replace("/", os.sep)
                entry = {"event_type": rec.get("event_type", "modified")}
                events.append((abs_path, entry))
            except Exception:
                pass

    modified = process_events(events, args.repo_root, rules, args.dry_run, logger)
    if modified:
        print(f"갱신 완료: {', '.join(Path(p).name for p in modified)}")
    else:
        print("갱신 대상 없음.")


if __name__ == "__main__":
    main()
