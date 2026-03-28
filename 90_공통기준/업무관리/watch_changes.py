"""
watch_changes.py — 업무리스트 파일 변경 감지 엔진 (Phase 1 + Phase 2 훅)
- Python watchdog 단일 프로세스
- 30분 idle debounce 후 JSONL 로그 기록
- 중복 실행 방지 (PID lock 파일)
- dry-run 모드 지원
- Phase 2: flush 후 commit_docs.process_events() 자동 호출 (설정 시)
"""

import argparse
import fnmatch
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ── 설정 로드 ──────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "auto_watch_config.yaml"


def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 경로 유틸 ──────────────────────────────────────────────────────────────

def is_excluded_dir(path: str, root: str, exclude_dirs: list) -> bool:
    rel = Path(os.path.relpath(path, root))
    for part in rel.parts:
        if part in exclude_dirs:
            return True
    return False


def is_excluded_pattern(filename: str, patterns: list) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False


def is_watched_extension(filename: str, extensions: list) -> bool:
    return Path(filename).suffix.lower() in extensions


def get_category(file_path: str, root: str) -> tuple:
    try:
        rel = Path(os.path.relpath(file_path, root))
        parts = rel.parts
        top = parts[0] if len(parts) >= 1 else ""
        sub = parts[1] if len(parts) >= 2 else ""
        return top, sub
    except ValueError:
        return "", ""


# ── 이벤트 병합 우선순위 ─────────────────────────────────────────────────

EVENT_PRIORITY = {"deleted": 4, "moved": 3, "created": 2, "modified": 1}


def merge_event_type(existing: str, incoming: str) -> str:
    if EVENT_PRIORITY.get(incoming, 0) > EVENT_PRIORITY.get(existing, 0):
        return incoming
    return existing


# ── 로그 파일 경로 ────────────────────────────────────────────────────────

def get_log_path(root: str, log_dir: str, prefix: str) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    return Path(root) / log_dir / f"{prefix}{date_str}.jsonl"


def get_error_log_path(root: str, log_dir: str, prefix: str) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    return Path(root) / log_dir / f"{prefix}{date_str}.log"


# ── 에러 로거 설정 ────────────────────────────────────────────────────────

def setup_error_logger(error_log_path: Path) -> logging.Logger:
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("watch_errors")
    logger.setLevel(logging.ERROR)
    handler = logging.FileHandler(error_log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    return logger


# ── Lock 파일 ─────────────────────────────────────────────────────────────

class LockFile:
    def __init__(self, path: Path):
        self.path = path

    def acquire(self) -> bool:
        if self.path.exists():
            try:
                existing_pid = int(self.path.read_text().strip())
                # 프로세스가 살아있는지 확인
                import psutil
                if psutil.pid_exists(existing_pid):
                    print(f"[ERROR] 이미 실행 중 (PID: {existing_pid}). 중복 실행 방지.")
                    return False
                else:
                    self.path.unlink()  # 좀비 lock 제거
            except Exception:
                self.path.unlink(missing_ok=True)

        self.path.write_text(str(os.getpid()))
        return True

    def release(self):
        self.path.unlink(missing_ok=True)


# ── 디바운서 ──────────────────────────────────────────────────────────────

class Debouncer:
    """
    동일 파일의 연속 이벤트를 마지막 이벤트 시각 기준 N분 idle 후 1건으로 확정.
    create/modify/move 이벤트는 병합, delete는 별도 기록.
    """

    def __init__(self, debounce_seconds: int):
        self.debounce_seconds = debounce_seconds
        self._pending: dict = {}  # abs_path → entry
        self._lock = threading.Lock()

    def add(self, event_type: str, abs_path: str, now: float = None):
        if now is None:
            now = time.time()
        with self._lock:
            if abs_path in self._pending:
                entry = self._pending[abs_path]
                entry["event_type"] = merge_event_type(entry["event_type"], event_type)
                entry["last_seen"] = now
                entry["raw_events"].append(event_type)
            else:
                self._pending[abs_path] = {
                    "event_type": event_type,
                    "first_seen": now,
                    "last_seen": now,
                    "raw_events": [event_type],
                }

    def flush_ready(self, now: float = None) -> list:
        """idle 시간 초과한 항목 반환 및 pending에서 제거."""
        if now is None:
            now = time.time()
        ready = []
        with self._lock:
            for path, entry in list(self._pending.items()):
                if now - entry["last_seen"] >= self.debounce_seconds:
                    ready.append((path, entry))
                    del self._pending[path]
        return ready

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)


# ── 이벤트 핸들러 ─────────────────────────────────────────────────────────

class WorkspaceEventHandler(FileSystemEventHandler):
    def __init__(self, cfg: dict, debouncer: Debouncer, error_logger: logging.Logger):
        super().__init__()
        self.root = cfg["watch"]["root"]
        self.exclude_dirs = cfg["watch"]["exclude_dirs"]
        self.exclude_patterns = cfg["watch"]["exclude_patterns"]
        self.watch_extensions = cfg["watch"]["watch_extensions"]
        self.debouncer = debouncer
        self.error_logger = error_logger

    def _should_skip(self, path: str) -> bool:
        filename = Path(path).name
        if is_excluded_dir(path, self.root, self.exclude_dirs):
            return True
        if is_excluded_pattern(filename, self.exclude_patterns):
            return True
        if not is_watched_extension(filename, self.watch_extensions):
            return True
        return False

    def on_created(self, event):
        if event.is_directory:
            return
        try:
            if not self._should_skip(event.src_path):
                self.debouncer.add("created", os.path.abspath(event.src_path))
        except Exception as e:
            self.error_logger.error(f"on_created 예외: {e} | {event.src_path}")

    def on_modified(self, event):
        if event.is_directory:
            return
        try:
            if not self._should_skip(event.src_path):
                self.debouncer.add("modified", os.path.abspath(event.src_path))
        except Exception as e:
            self.error_logger.error(f"on_modified 예외: {e} | {event.src_path}")

    def on_moved(self, event):
        if event.is_directory:
            return
        try:
            # 이동 후 경로 기준으로 기록
            dest = event.dest_path
            if not self._should_skip(dest):
                self.debouncer.add("moved", os.path.abspath(dest))
        except Exception as e:
            self.error_logger.error(f"on_moved 예외: {e} | {event.src_path}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        try:
            if not self._should_skip(event.src_path):
                self.debouncer.add("deleted", os.path.abspath(event.src_path))
        except Exception as e:
            self.error_logger.error(f"on_deleted 예외: {e} | {event.src_path}")


# ── 로그 라이터 ───────────────────────────────────────────────────────────

def write_log_entries(entries: list, cfg: dict, dry_run: bool, error_logger: logging.Logger):
    if not entries:
        return

    root = cfg["watch"]["root"]
    log_dir = cfg["logging"]["log_dir"]
    log_prefix = cfg["logging"]["log_prefix"]
    log_path = get_log_path(root, log_dir, log_prefix)

    batch_id = str(uuid.uuid4())[:8]

    records = []
    for abs_path, entry in entries:
        try:
            file_name = Path(abs_path).name
            extension = Path(abs_path).suffix.lower()
            category_top, category_sub = get_category(abs_path, root)
            first_ts = datetime.fromtimestamp(entry["first_seen"]).isoformat()
            last_ts = datetime.fromtimestamp(entry["last_seen"]).isoformat()
            debounce_sec = round(entry["last_seen"] - entry["first_seen"])

            record = {
                "timestamp": last_ts,
                "batch_id": batch_id,
                "event_type": entry["event_type"],
                "file_path": abs_path.replace("\\", "/"),
                "file_name": file_name,
                "extension": extension,
                "category_top": category_top,
                "category_sub": category_sub,
                "is_allowed_path": True,
                "is_excluded": False,
                "debounce_seconds": debounce_sec,
                "first_seen": first_ts,
                "raw_event_count": len(entry["raw_events"]),
                "note": f"raw_events: {','.join(set(entry['raw_events']))}",
            }
            records.append(record)
        except Exception as e:
            error_logger.error(f"로그 레코드 생성 실패: {e} | {abs_path}")

    if dry_run:
        for r in records:
            print(f"[DRY-RUN] {r['timestamp']} | {r['event_type']:8s} | {r['file_name']}")
        return

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception as e:
        error_logger.error(f"로그 파일 쓰기 실패: {e} | {log_path}")


# ── 플러시 워커 스레드 ────────────────────────────────────────────────────

def _try_phase3_update(ready: list, repo_root: str, dry_run: bool,
                       error_logger: logging.Logger) -> list:
    """
    Phase 3 update_status_tasks 훅.
    반환: 갱신된 파일 이벤트 목록 (Phase 2에 합산용).
    미설치 시 조용히 건너뜀.
    """
    try:
        import update_status_tasks as _ust
        rules = _ust.load_rules()
        modified = _ust.process_events(ready, repo_root, rules, dry_run, error_logger)
        # 갱신된 STATUS/TASKS를 Phase 2 커밋 대상에 추가
        extra = []
        for abs_path in modified:
            extra.append((abs_path, {
                "event_type": "modified",
                "first_seen": time.time(),
                "last_seen": time.time(),
                "raw_events": ["modified"],
            }))
        return extra
    except ImportError:
        pass
    except Exception as e:
        error_logger.error(f"Phase 3 훅 예외: {e}")
    return []


def _try_phase2_commit(ready: list, dry_run: bool, error_logger: logging.Logger) -> dict:
    """Phase 2 commit_docs 훅. 미설치 시 조용히 건너뜀. 반환: phase2 결과 dict."""
    try:
        from pathlib import Path as _Path
        import commit_docs as _cd
        commit_cfg_path = _Path(__file__).parent / "auto_commit_config.yaml"
        if not commit_cfg_path.exists():
            return {}
        commit_cfg = _cd.load_config(commit_cfg_path)
        result = _cd.process_events(ready, commit_cfg, dry_run, error_logger)
        return result or {}
    except ImportError:
        pass  # commit_docs 미설치 — Phase 1 단독 모드
    except Exception as e:
        error_logger.error(f"Phase 2 훅 예외: {e}")
    return {}


def _try_phase4_notify(batch_id: str, ready: list, phase3_result: dict,
                       phase2_result: dict, dry_run: bool,
                       error_logger: logging.Logger):
    """Phase 4 Slack 알림 훅. 미설치 시 조용히 건너뜀."""
    try:
        import slack_notify as _sn
        notify_cfg = _sn.load_config()
        _sn.notify_batch(
            batch_id=batch_id,
            events=ready,
            phase3_result=phase3_result,
            phase2_result=phase2_result,
            cfg=notify_cfg,
            dry_run=dry_run,
            logger=error_logger,
        )
    except ImportError:
        pass  # slack_notify 미설치 — Phase 1~3 단독 모드
    except Exception as e:
        error_logger.error(f"Phase 4 훅 예외: {e}")


def flush_worker(debouncer: Debouncer, cfg: dict, dry_run: bool,
                 error_logger: logging.Logger, stop_event: threading.Event):
    """60초마다 debounce 완료 항목을 로그에 기록하고 Phase 3 → Phase 2 → Phase 4 순으로 훅 호출."""
    import uuid as _uuid
    repo_root = cfg["watch"]["root"]
    while not stop_event.is_set():
        stop_event.wait(timeout=60)
        try:
            ready = debouncer.flush_ready()
            if ready:
                batch_id = str(_uuid.uuid4())[:8]
                write_log_entries(ready, cfg, dry_run, error_logger)
                extra = _try_phase3_update(ready, repo_root, dry_run, error_logger)
                phase3_result = {
                    "ok": len(extra) > 0,
                    "modified": [p for p, _ in extra],
                }
                phase2_result = _try_phase2_commit(ready + extra, dry_run, error_logger)
                _try_phase4_notify(batch_id, ready, phase3_result, phase2_result,
                                   dry_run, error_logger)
        except Exception as e:
            error_logger.error(f"flush_worker 예외: {e}")

    # 종료 시 남은 항목 최종 플러시
    try:
        ready = debouncer.flush_ready(now=time.time() + 999999)
        if ready:
            batch_id = str(_uuid.uuid4())[:8]
            write_log_entries(ready, cfg, dry_run, error_logger)
            extra = _try_phase3_update(ready, repo_root, dry_run, error_logger)
            phase3_result = {
                "ok": len(extra) > 0,
                "modified": [p for p, _ in extra],
            }
            phase2_result = _try_phase2_commit(ready + extra, dry_run, error_logger)
            _try_phase4_notify(batch_id, ready, phase3_result, phase2_result,
                               dry_run, error_logger)
    except Exception as e:
        error_logger.error(f"종료 시 최종 플러시 실패: {e}")


# ── 메인 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="업무리스트 파일 변경 감시 엔진")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="설정 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="로그 파일 미생성, 콘솔 출력만")
    args = parser.parse_args()

    # 설정 로드
    cfg = load_config(Path(args.config))
    root = Path(cfg["watch"]["root"])
    lock_filename = cfg["lock"]["file"]
    lock_path = root / lock_filename

    # 에러 로거
    error_log_path = get_error_log_path(
        cfg["watch"]["root"],
        cfg["logging"]["log_dir"],
        cfg["logging"]["error_prefix"],
    )
    error_logger = setup_error_logger(error_log_path)

    # Lock 획득 (dry-run은 lock 생략)
    lock = LockFile(lock_path)
    if not args.dry_run:
        if not lock.acquire():
            sys.exit(1)

    debounce_sec = int(cfg["watch"]["debounce_minutes"]) * 60
    debouncer = Debouncer(debounce_sec)
    stop_event = threading.Event()

    handler = WorkspaceEventHandler(cfg, debouncer, error_logger)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)

    flush_thread = threading.Thread(
        target=flush_worker,
        args=(debouncer, cfg, args.dry_run, error_logger, stop_event),
        daemon=True,
    )

    try:
        observer.start()
        flush_thread.start()
        mode = "[DRY-RUN] " if args.dry_run else ""
        print(f"{mode}감시 시작: {root}")
        print(f"디바운스: {cfg['watch']['debounce_minutes']}분 | Ctrl+C로 종료")

        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n종료 중...")
    except Exception as e:
        error_logger.error(f"메인 루프 예외: {e}")
    finally:
        observer.stop()
        observer.join()
        stop_event.set()
        flush_thread.join(timeout=10)
        if not args.dry_run:
            lock.release()
        print("종료 완료.")


if __name__ == "__main__":
    main()
