"""
commit_docs.py — GitHub 자동 커밋 엔진 (Phase 2)
- Phase 1 flush 이벤트를 받아 allowlist 기준으로 git add/commit/push
- dry-run 모드 지원
- 실패 시 원본 파일 변경 없음, 오류 로그만 기록
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import yaml

# ── 설정 로드 ──────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "auto_commit_config.yaml"


def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 에러 로거 ─────────────────────────────────────────────────────────────

def setup_error_logger(cfg: dict) -> logging.Logger:
    root = cfg["repo"]["path"]
    log_dir = cfg["logging"]["log_dir"]
    prefix = cfg["logging"]["error_prefix"]
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = Path(root) / log_dir / f"{prefix}{date_str}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("commit_errors")
    if not logger.handlers:
        logger.setLevel(logging.ERROR)
        h = logging.FileHandler(log_path, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(h)
    return logger


# ── allowlist / blocklist 매칭 ────────────────────────────────────────────

def _matches_any(rel_path: str, patterns: list) -> bool:
    p = Path(rel_path)
    for pat in patterns:
        try:
            if p.match(pat):
                return True
            # 파일명만으로도 체크 (루트 레벨 파일 대응)
            if Path(p.name).match(pat):
                return True
        except Exception:
            pass
    return False


def is_committable(abs_path: str, repo_root: str, cfg: dict) -> bool:
    """allowlist에 포함되고 blocklist에 없는 경우만 True."""
    try:
        rel = Path(os.path.relpath(abs_path, repo_root)).as_posix()
    except ValueError:
        return False

    blocklist = cfg["blocklist"]["patterns"]
    allowlist = cfg["allowlist"]["patterns"]

    if _matches_any(rel, blocklist):
        return False
    if _matches_any(rel, allowlist):
        return True
    return False


# ── 커밋 메시지 결정 ──────────────────────────────────────────────────────

def determine_commit_message(files_with_events: list, cfg: dict) -> str:
    """
    files_with_events: [(rel_path, event_type), ...]
    우선순위: STATUS/TASKS > script > skill > config > docs > default
    """
    rules = cfg["commit"]["rules"]
    default_prefix = cfg["commit"]["default_prefix"]
    default_desc = cfg["commit"]["default_description"]

    file_names = [Path(f).name for f, _ in files_with_events]
    extensions = [Path(f).suffix.lower() for f, _ in files_with_events]
    event_types = [e for _, e in files_with_events]

    for rule in rules:
        if "match_names" in rule:
            if any(n in rule["match_names"] for n in file_names):
                return f"{rule['prefix']}: {rule['description']}"
        if "match_exts" in rule:
            if any(ext in rule["match_exts"] for ext in extensions):
                if "event_modified" in rule:
                    # 수정 vs 신규 구분
                    prefix = rule["event_created"] if "created" in event_types else rule["event_modified"]
                else:
                    prefix = rule.get("prefix", default_prefix)
                return f"{prefix}: {rule['description']}"

    return f"{default_prefix}: {default_desc}"


def build_commit_body(files_with_events: list, batch_id: str) -> str:
    lines = [f"batch: {batch_id}", ""]
    for rel, event in sorted(files_with_events):
        lines.append(f"  {event:8s} {rel}")
    lines.append("")
    lines.append("Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>")
    return "\n".join(lines)


# ── Git 유틸 ─────────────────────────────────────────────────────────────

def git_run(args: list, cwd: str, timeout: int = 30) -> tuple:
    """(returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def git_current_branch(repo: str) -> str:
    rc, out, _ = git_run(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    return out if rc == 0 else ""


def git_stage_files(files: list, repo: str) -> tuple:
    rc, out, err = git_run(["add", "--"] + files, repo)
    return rc, err


def git_is_staged(repo: str) -> bool:
    rc, out, _ = git_run(["diff", "--cached", "--name-only"], repo)
    return rc == 0 and bool(out.strip())


def git_commit(message: str, author_name: str, author_email: str, repo: str) -> tuple:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_AUTHOR_EMAIL"] = author_email
    env["GIT_COMMITTER_NAME"] = author_name
    env["GIT_COMMITTER_EMAIL"] = author_email
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            env=env,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def git_push(repo: str, branch: str, timeout: int = 60) -> tuple:
    rc, out, err = git_run(["push", "origin", branch], repo, timeout=timeout)
    return rc, err


# ── 커밋 로그 기록 ────────────────────────────────────────────────────────

def write_commit_log(record: dict, cfg: dict):
    root = cfg["repo"]["path"]
    log_dir = cfg["logging"]["log_dir"]
    prefix = cfg["logging"]["commit_log_prefix"]
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = Path(root) / log_dir / f"{prefix}{date_str}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── 상태 파일 (중복 커밋 방지) ────────────────────────────────────────────

def load_state(cfg: dict) -> dict:
    root = cfg["repo"]["path"]
    log_dir = cfg["logging"]["log_dir"]
    state_file = cfg["logging"]["state_file"]
    path = Path(root) / log_dir / state_file
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed_batch_ids": []}


def save_state(state: dict, cfg: dict):
    root = cfg["repo"]["path"]
    log_dir = cfg["logging"]["log_dir"]
    state_file = cfg["logging"]["state_file"]
    path = Path(root) / log_dir / state_file
    # 최근 200개 batch_id만 유지
    ids = state.get("processed_batch_ids", [])
    state["processed_batch_ids"] = ids[-200:]
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 핵심: 이벤트 처리 ─────────────────────────────────────────────────────

def process_events(
    events: list,
    cfg: dict,
    dry_run: bool = False,
    error_logger: logging.Logger = None,
) -> dict:
    """
    events: [(abs_path, entry_dict), ...]  ← Phase 1 debouncer.flush_ready() 결과
    Returns: {"committed": int, "skipped": int, "failed": int, "commit_sha": str}
    """
    if error_logger is None:
        error_logger = setup_error_logger(cfg)

    repo = cfg["repo"]["path"]
    branch = cfg["repo"]["branch"]
    push_on_commit = cfg["repo"].get("push_on_commit", True)
    push_timeout = cfg["repo"].get("push_timeout_seconds", 60)
    author_name = cfg["commit"]["author_name"]
    author_email = cfg["commit"]["author_email"]

    result = {"committed": 0, "skipped": 0, "failed": 0, "commit_sha": ""}

    if not events:
        return result

    batch_id = str(uuid.uuid4())[:8]

    # delete 이벤트 별도 처리 (즉시 후속 작업 금지)
    committable = []
    for abs_path, entry in events:
        event_type = entry["event_type"]
        if event_type == "deleted":
            result["skipped"] += 1
            continue
        if not is_committable(abs_path, repo, cfg):
            result["skipped"] += 1
            continue
        try:
            rel = Path(os.path.relpath(abs_path, repo)).as_posix()
        except ValueError:
            result["skipped"] += 1
            continue
        committable.append((abs_path, rel, event_type))

    if not committable:
        return result

    # 파일 존재 확인 (이동/삭제 후 없을 수 있음)
    existing = []
    for abs_path, rel, event_type in committable:
        if Path(abs_path).exists():
            existing.append((abs_path, rel, event_type))
        else:
            result["skipped"] += 1

    if not existing:
        return result

    files_with_events = [(rel, ev) for _, rel, ev in existing]
    abs_files = [abs_p for abs_p, _, _ in existing]
    rel_files = [rel for _, rel, _ in existing]

    commit_subject = determine_commit_message(files_with_events, cfg)
    commit_body = build_commit_body(files_with_events, batch_id)
    full_message = f"{commit_subject}\n\n{commit_body}"

    if dry_run:
        print(f"[DRY-RUN] batch={batch_id} | {commit_subject}")
        for rel, ev in files_with_events:
            print(f"  {ev:8s} {rel}")
        result["committed"] = len(existing)
        return result

    try:
        # branch 확인
        current = git_current_branch(repo)
        if current != branch:
            error_logger.error(f"브랜치 불일치: current={current}, expect={branch}")
            result["failed"] += len(existing)
            return result

        # git add
        rc, err = git_stage_files(rel_files, repo)
        if rc != 0:
            error_logger.error(f"git add 실패: {err}")
            result["failed"] += len(existing)
            return result

        # staged 확인
        if not git_is_staged(repo):
            # 변경 없음 (이미 동일 내용)
            result["skipped"] += len(existing)
            return result

        # git commit
        rc, out, err = git_commit(full_message, author_name, author_email, repo)
        if rc != 0:
            error_logger.error(f"git commit 실패: {err}")
            result["failed"] += len(existing)
            return result

        # SHA 추출
        rc2, sha, _ = git_run(["rev-parse", "--short", "HEAD"], repo)
        result["commit_sha"] = sha if rc2 == 0 else ""
        result["committed"] = len(existing)

        # git push
        push_err = ""
        if push_on_commit:
            rc_push, push_err = git_push(repo, branch, push_timeout)
            if rc_push != 0:
                error_logger.error(f"git push 실패: {push_err}")

        # 커밋 로그 기록
        write_commit_log(
            {
                "timestamp": datetime.now().isoformat(),
                "batch_id": batch_id,
                "commit_sha": result["commit_sha"],
                "commit_message": commit_subject,
                "files": rel_files,
                "push_ok": push_on_commit and push_err == "",
                "dry_run": False,
            },
            cfg,
        )

    except Exception as e:
        error_logger.error(f"process_events 예외: {e}")
        result["failed"] += len(existing)

    return result


# ── JSONL 로그 기반 독립 실행 모드 ───────────────────────────────────────

def run_from_log(log_path: Path, cfg: dict, dry_run: bool, error_logger):
    """
    JSONL 로그에서 미처리 항목을 읽어 커밋.
    이미 처리된 batch_id는 건너뜀.
    """
    state = load_state(cfg)
    processed_ids = set(state.get("processed_batch_ids", []))

    if not log_path.exists():
        print(f"로그 파일 없음: {log_path}")
        return

    entries_by_batch: dict = {}
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                bid = rec.get("batch_id", "")
                if bid in processed_ids:
                    continue
                if bid not in entries_by_batch:
                    entries_by_batch[bid] = []
                entries_by_batch[bid].append(rec)
            except Exception:
                pass

    if not entries_by_batch:
        print("처리할 신규 항목 없음.")
        return

    total_committed = 0
    for bid, records in entries_by_batch.items():
        # JSONL 레코드를 process_events 형식으로 변환
        events = []
        for rec in records:
            abs_path = rec.get("file_path", "").replace("/", os.sep)
            entry = {
                "event_type": rec.get("event_type", "modified"),
                "first_seen": 0,
                "last_seen": 0,
                "raw_events": [rec.get("event_type", "modified")],
            }
            events.append((abs_path, entry))

        res = process_events(events, cfg, dry_run, error_logger)
        total_committed += res["committed"]

        if not dry_run:
            processed_ids.add(bid)

    if not dry_run:
        state["processed_batch_ids"] = list(processed_ids)
        save_state(state, cfg)

    print(f"처리 완료: {total_committed}건 커밋")


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="업무리스트 GitHub 자동 커밋")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-file", help="처리할 JSONL 로그 파일 (미지정 시 오늘 날짜)")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    error_logger = setup_error_logger(cfg)

    if args.log_file:
        log_path = Path(args.log_file)
    else:
        root = cfg["repo"]["path"]
        log_dir = cfg["logging"].get("watch_log_dir", cfg["logging"]["log_dir"])
        date_str = datetime.now().strftime("%Y%m%d")
        log_path = Path(root) / log_dir / f"작업로그_{date_str}.jsonl"

    run_from_log(log_path, cfg, args.dry_run, error_logger)


if __name__ == "__main__":
    main()
