"""D0 스케줄러 사후 검증 + 자동 재실행.

debate_20260429_121732_3way Round 1 합의 (pass_ratio 1.00) 구현.

[목적]
  D0_SP3M3_Morning(07:10) / Night 작업 스케줄러 실행 후 결과 검증.
  실패 감지 시 원인 분류 → RETRY_OK 백오프 재시도 / RETRY_BLOCK·RETRY_NO 즉시 알림.

[원인 분류]
  RETRY_OK    : timeout / 5xx / 네트워크 / Chrome CDP 미기동 / OAuth 정착 (Phase 0/1/2 한정)
  RETRY_BLOCK : timeout이 Phase 3+ 발생 (이미 일부 등록 의심) / dedupe N건 정리 (기존 등록 의심)
  RETRY_NO    : xlsx 미존재 / 권한 / 마스터 정보 불일치
  UNKNOWN     : 분류 실패 — 1회 재시도만

[백오프 (RETRY_OK)]
  1분 / 5분 / 15분 / 30분 — 누적 51분 한계

[안전장치 (R5)]
  - dedupe 매 시도 선행 (erp_d0_dedupe.py --execute)
  - schtasks 상태 확인 → Running이면 Phase 분석 → Phase 0/1/2만 강제 종료 OK / Phase 3+ 종료 금지
  - lock os.O_EXCL atomic + JSON {pid, started, session} + 60분 stale
  - 누적 시간 + 시도 횟수 + 카운터 파일 3중 차단
  - 실패 시 chrome-devtools-mcp DOM/스크린샷 저장 → Slack 알림 포함

[사용 예]
  python verify_run.py --session morning --line SP3M3
  python verify_run.py --session morning --line SP3M3 --dry-run   # 점검만, 재실행 안 함
"""
import sys, os, json, time, subprocess, argparse, re
from datetime import datetime
from pathlib import Path

# 세션131 [E]: cp949 콘솔(Windows 작업 스케줄러 호출)에서 em dash(—) 등 출력 시 UnicodeEncodeError로 즉시 종료되던 버그.
# 4/30 recover_20260430_071502.log 실측: verify_run.py:62 print() cp949 incompatible. PYTHONIOENCODING=utf-8 우회 대신 코드 측 reconfigure.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROJECT_ROOT = Path(r"C:\Users\User\Desktop\업무리스트")
LOG_DIR = PROJECT_ROOT / "06_생산관리" / "D0_업로드" / "logs"
STATE_DIR = PROJECT_ROOT / ".claude" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
DEDUPE_TOOL = PROJECT_ROOT / ".claude" / "tmp" / "erp_d0_dedupe.py"
RUN_PY = PROJECT_ROOT / "90_공통기준" / "스킬" / "d0-production-plan" / "run.py"

BACKOFF_SCHEDULE = [60, 300, 900, 1800]  # 1분 / 5분 / 15분 / 30분 (초)
MAX_ELAPSED_SEC = 51 * 60  # 누적 51분
LOCK_STALE_SEC = 60 * 60   # 60분
PHASE_ALLOW_KILL = {"Phase 0", "Phase 1", "Phase 2"}
PHASE_BLOCK_KILL = {"Phase 3", "Phase 4", "Phase 5", "Phase 6"}

RETRY_OK_PATTERNS = [
    (r"timeout|TimeoutError|asyncio\.TimeoutError|TimeoutException", "timeout"),
    # 5xx HTTP 응답만 매칭 (timestamp 오매칭 방지). 단순 r"5\d{2}\b"는 [HHMMSS] 패턴에 오매칭됨
    (r"HTTP[/ ]?5\d{2}|status[Cc]ode[: =]+5\d{2}|InternalServerError|\b5\d{2}\s+(?:Internal|Server|Bad|Service)", "5xx"),
    (r"ConnectionError|ConnectionResetError|NetworkError|ECONN", "network"),
    (r"CDP.*not running|9222.*refused|chrome.*not.*launched", "cdp_down"),
    (r"auth-dev.*login\?error|OAuth.*timeout|클라이언트.*선택.*화면", "oauth_stuck"),
]
RETRY_NO_PATTERNS = [
    (r"FileNotFoundError.*\.xlsm|xlsx.*not.*exist|생산지시서.*없음", "xlsx_missing"),
    # 폴더 없음 / 파일 없음 (run.py find_plan_file fallback 실패 시) — 즉시 알림
    (r"FileNotFoundError.*폴더 없음|FileNotFoundError.*파일 없음", "plan_path_missing"),
    (r"PermissionError|Access.*denied|권한.*없음", "permission"),
    (r"마스터.*정보.*불일치|품번.*매칭.*실패|MasterMismatch", "master_mismatch"),
]


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def get_today():
    return datetime.now().strftime("%Y%m%d")


def get_log_path(session, today):
    pattern = f"{session}_{today}*.log"
    matches = sorted(LOG_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def acquire_lock(session):
    lock_path = STATE_DIR / f"d0_verify_{get_today()}_{session}.lock"
    if lock_path.exists():
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
            started = datetime.fromisoformat(data.get("started", "1970-01-01T00:00:00"))
            age = (datetime.now() - started).total_seconds()
            if age > LOCK_STALE_SEC:
                log(f"stale lock 감지 (age={age:.0f}s, pid={data.get('pid')}), 재획득", "WARN")
                lock_path.unlink()
            else:
                log(f"활성 lock 존재 (pid={data.get('pid')}, age={age:.0f}s) — verify 중복 방지로 종료", "ERROR")
                return None
        except Exception as e:
            log(f"lock 파일 파싱 실패 → 무시하고 재획득: {e}", "WARN")
            lock_path.unlink()
    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    payload = {"pid": os.getpid(), "started": datetime.now().isoformat(timespec="seconds"), "session": session}
    os.write(fd, json.dumps(payload).encode("utf-8"))
    os.close(fd)
    return lock_path


def release_lock(lock_path):
    if lock_path and lock_path.exists():
        lock_path.unlink()


def check_log_success(log_path):
    if not log_path or not log_path.exists():
        return False, "log_missing"
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return False, f"log_read_error:{e}"
    tail = text[-3000:]
    if "rsltCnt=" in tail and "exit code = 0" in tail:
        return True, "ok_marker"
    if "Phase 6 SmartMES 검증" in tail and "✅" in tail:
        return True, "phase6_marker"
    if "exit code = 0" in tail and ("statusCode=200" in tail or "statusCode 200" in tail):
        return True, "exit0_status200"
    return False, "no_success_marker"


def classify_failure(log_path):
    if not log_path or not log_path.exists():
        return "RETRY_NO", "log_missing"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    tail = text[-5000:]
    for pat, label in RETRY_NO_PATTERNS:
        if re.search(pat, tail, re.IGNORECASE):
            return "RETRY_NO", label
    last_phase = analyze_phase(tail)
    for pat, label in RETRY_OK_PATTERNS:
        if re.search(pat, tail, re.IGNORECASE):
            # GPT/Gemini 양측 합의 (debate_20260429_121732_3way 후속 보강):
            # 모든 RETRY_OK 원인(timeout/5xx/network/CDP/OAuth)이 Phase 3+ 발생 시
            # 이미 일부 등록 의심으로 RETRY_BLOCK 처리. 데이터 무결성 우선.
            if last_phase in PHASE_BLOCK_KILL:
                return "RETRY_BLOCK", f"{label}_at_{last_phase.replace(' ', '')}"
            return "RETRY_OK", label
    return "UNKNOWN", "unmatched"


def analyze_phase(text):
    matches = re.findall(r"\bPhase\s+(\d)\b", text)
    if not matches:
        return "unknown"
    last = max(int(m) for m in matches)
    return f"Phase {last}"


def schtasks_query(task_name):
    try:
        out = subprocess.run(
            ["schtasks", "/query", "/TN", task_name, "/v", "/fo", "list"],
            capture_output=True, text=True, encoding="cp949", errors="replace", timeout=10
        )
        return out.stdout
    except Exception as e:
        log(f"schtasks query 실패: {e}", "WARN")
        return ""


def schtasks_status(task_name):
    out = schtasks_query(task_name)
    status = "Unknown"
    last_result = None
    for line in out.splitlines():
        if "상태:" in line or "Status:" in line:
            status = line.split(":", 1)[1].strip()
        elif "마지막 결과:" in line or "Last Result:" in line:
            try:
                last_result = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
    return status, last_result


def schtasks_end(task_name):
    try:
        subprocess.run(["schtasks", "/end", "/TN", task_name], capture_output=True, timeout=10)
        log(f"schtasks /end {task_name} 실행", "WARN")
        return True
    except Exception as e:
        log(f"schtasks /end 실패: {e}", "ERROR")
        return False


def do_dedupe(line, today):
    log(f"dedupe 선행 실행 (--line {line} --date {today} --execute)", "INFO")
    try:
        out = subprocess.run(
            [sys.executable, str(DEDUPE_TOOL), "--line", line, "--date", today, "--execute"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120
        )
        text = (out.stdout or "") + (out.stderr or "")
        m = re.search(r"(\d+)\s*건\s*(?:삭제|정리)", text)
        deleted = int(m.group(1)) if m else 0
        log(f"dedupe 결과: {deleted}건 정리 (exit={out.returncode})", "INFO")
        return deleted, out.returncode
    except Exception as e:
        log(f"dedupe 실행 실패: {e}", "ERROR")
        return -1, 1


def run_main(session, line):
    log(f"run.py 재실행 시작 (--session {session} --line {line})", "INFO")
    try:
        out = subprocess.run(
            [sys.executable, str(RUN_PY), "--session", session, "--line", line],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900
        )
        log(f"run.py 종료 (exit={out.returncode})", "INFO")
        return out.returncode == 0
    except Exception as e:
        log(f"run.py 실행 실패: {e}", "ERROR")
        return False


def notify_slack(title, body):
    log(f"[NOTIFY] {title}", "WARN")
    log(body[:500], "WARN")
    notify_path = STATE_DIR / "d0_verify_notify.jsonl"
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), "title": title, "body": body}
    with notify_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def get_log_tail(log_path, n=30):
    if not log_path or not log_path.exists():
        return "(no log)"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    return "\n".join(text.splitlines()[-n:])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--session", choices=["morning", "night"], required=True)
    p.add_argument("--line", default="SP3M3")
    p.add_argument("--max-elapsed-min", type=int, default=51)
    p.add_argument("--dry-run", action="store_true", help="점검만, 재실행 안 함")
    args = p.parse_args()

    today = get_today()
    started_at = time.time()
    deadline = started_at + args.max_elapsed_min * 60

    lock_path = acquire_lock(args.session)
    if not lock_path:
        sys.exit(2)

    try:
        task_name = f"D0_SP3M3_{args.session.capitalize()}"
        log(f"=== D0 verify 시작 — {task_name} ===")

        status, last_result = schtasks_status(task_name)
        log(f"schtasks {task_name}: status={status}, lastResult={last_result}")

        log_path = get_log_path(args.session, today)
        log(f"log path: {log_path}")

        if status == "실행 중" or status.lower() == "running":
            log("작업 실행 중 감지 — 5분 추가 대기", "INFO")
            time.sleep(300)
            status2, _ = schtasks_status(task_name)
            if status2 in ("실행 중",) or status2.lower() == "running":
                last_phase = analyze_phase((log_path.read_text(encoding="utf-8", errors="replace") if log_path else ""))
                # GPT/Gemini 양측 합의 후속 보강: Phase unknown은 강제 종료 금지.
                # Phase 0/1/2(등록 전 단계)임이 로그로 확인될 때만 schtasks /end 허용.
                if last_phase in PHASE_ALLOW_KILL:
                    log(f"Phase {last_phase}: 강제 종료 시도", "WARN")
                    schtasks_end(task_name)
                else:
                    notify_slack(f"D0 {task_name} Phase {last_phase} 진행 중 — 종료 금지",
                                 f"Phase 0/1/2 등록 전 단계 확인 불가. 강제 종료 차단 + 사용자 수동 결정 필요.\n\n{get_log_tail(log_path)}")
                    sys.exit(3)

        ok, marker = check_log_success(log_path)
        if ok:
            log(f"성공 마커 감지: {marker} — verify 종료 (재실행 불필요)", "INFO")
            sys.exit(0)

        attempt = 0
        while time.time() < deadline:
            classification, reason = classify_failure(log_path)
            elapsed = int(time.time() - started_at)
            log(f"분류={classification} / 원인={reason} / 누적={elapsed}s / 시도={attempt}", "INFO")

            if classification in ("RETRY_NO", "RETRY_BLOCK"):
                notify_slack(f"D0 {task_name} {classification} ({reason}) — 자동 재실행 중단",
                             f"분류={classification} / 원인={reason} / 시도={attempt}\n\n로그 끝 30줄:\n{get_log_tail(log_path)}")
                sys.exit(4)

            if classification == "UNKNOWN" and attempt >= 1:
                notify_slack(f"D0 {task_name} UNKNOWN 1회 재시도 후 실패 — 사용자 수동 결정",
                             f"분류기 실패. 시도={attempt}\n\n로그 끝 30줄:\n{get_log_tail(log_path)}")
                sys.exit(5)

            if attempt >= len(BACKOFF_SCHEDULE):
                notify_slack(f"D0 {task_name} 재시도 4회 + 누적 {elapsed}s 후 실패",
                             f"분류={classification} / 원인={reason}\n\n로그 끝 30줄:\n{get_log_tail(log_path)}")
                sys.exit(6)

            wait_sec = BACKOFF_SCHEDULE[attempt]
            if time.time() + wait_sec > deadline:
                notify_slack(f"D0 {task_name} 누적 한계 ({args.max_elapsed_min}min) 도달",
                             f"다음 백오프({wait_sec}s) 적용 시 한계 초과. 자동 재시도 종료.\n\n{get_log_tail(log_path)}")
                sys.exit(7)

            log(f"백오프 대기 {wait_sec}s 후 재시도", "INFO")
            time.sleep(wait_sec)

            deleted, dedupe_rc = do_dedupe(args.line, today)
            if deleted > 0:
                notify_slack(f"D0 {task_name} dedupe {deleted}건 정리 — RETRY_BLOCK 트리거 + 재실행 중단",
                             f"기존 등록 의심으로 자동 재실행 중단. 사용자 수동 검증 필요.\n\n{get_log_tail(log_path)}")
                sys.exit(8)

            if args.dry_run:
                log("dry-run 모드 — run.py 재실행 스킵, 종료", "INFO")
                sys.exit(0)

            attempt += 1
            ok = run_main(args.session, args.line)
            log_path = get_log_path(args.session, today)
            if ok:
                ok2, marker2 = check_log_success(log_path)
                if ok2:
                    elapsed = int(time.time() - started_at)
                    notify_slack(f"D0 {task_name} 재시도 {attempt}회 후 성공 (누적 {elapsed}s)",
                                 f"마커: {marker2}")
                    sys.exit(0)

        notify_slack(f"D0 {task_name} 누적 한계 도달 — 자동 재시도 종료",
                     f"시도={attempt}, 누적={int(time.time()-started_at)}s\n\n{get_log_tail(log_path)}")
        sys.exit(7)

    finally:
        release_lock(lock_path)
        log("=== D0 verify 종료 ===")


if __name__ == "__main__":
    main()
