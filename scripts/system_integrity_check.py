# VELOS 운영 철학 선언문: 파일명 고정, 자가 검증 필수, 결과 기록, 경로/구조 불변, 실패 시 안전 복구와 알림.
import os, sys, json, time, sqlite3
from pathlib import Path

ROOT = "C:/giwanos"
HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")

AUTOSAVE_REQUIRED = os.getenv("VELOS_AUTOSAVE_REQUIRED", "0") in ("1","true","True","YES","yes")

def _log_info(h, key, value):
    h[key] = value
    h.setdefault("notes", []).append(f"{key}: {value}")

def jload(p):
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}

def jwrite(p, data):
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to write {p}: {e}")

def check_file_integrity():
    """핵심 파일들의 존재성과 접근 가능성 점검"""
    critical_files = [
        "data/memory/memory_buffer.jsonl",
        "data/memory/learning_memory.json",
        "data/memory/velos.db",
        "data/logs/system_health.json",
        "scripts/run_giwanos_master_loop.py",
        "scripts/velos_bridge.py",
        "modules/core/memory_adapter.py",
        "modules/core/context_builder.py"
    ]

    issues = []
    for file_path in critical_files:
        full_path = os.path.join(ROOT, file_path)
        if not os.path.exists(full_path):
            issues.append(f"missing:{file_path}")
        elif not os.access(full_path, os.R_OK):
            issues.append(f"no_read:{file_path}")

    return issues

def check_db_integrity():
    """데이터베이스 무결성 점검"""
    issues = []

    # velos.db 점검 (올바른 DB 파일)
    db_path = os.path.join(ROOT, "data", "memory", "velos.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM memory")
            count = cur.fetchone()[0]
            conn.close()
        except Exception as e:
            issues.append(f"db_corrupt:velos_memory.db - {e}")
    else:
        issues.append("missing:velos_memory.db")

    return issues

def check_process_health():
    """프로세스 상태 점검"""
    issues = []

    # autosave_runner 프로세스 점검
    try:
        import subprocess, json
        # PowerShell로 프로세스 조회
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'autosave_runner\\.ps1' } | "
            "Select-Object ProcessId,CommandLine | ConvertTo-Json"
        ]
        out = subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.DEVNULL)
        procs = json.loads(out) if out.strip() else []
        count = (len(procs) if isinstance(procs, list) else (1 if procs else 0))

        if count >= 1:
            # 프로세스가 실행 중이면 정상
            pass
        else:
            if AUTOSAVE_REQUIRED:
                issues.append("process_missing:autosave_runner")
            else:
                # 기본은 INFO로 처리 (경고하지 않음)
                pass
    except Exception as e:
        issues.append(f"process_check_failed:{e}")

    return issues

def check_autosave_runner(h):
    """
    autosave_runner 프로세스 존재 여부 확인.
    기본: 없어도 정상(INFO). 필요 시 환경변수로 강제.
    """
    try:
        import subprocess, json
        # PowerShell로 프로세스 조회
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'autosave_runner\\.ps1' } | "
            "Select-Object ProcessId,CommandLine | ConvertTo-Json"
        ]
        out = subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.DEVNULL)
        procs = json.loads(out) if out.strip() else []
        count = (len(procs) if isinstance(procs, list) else (1 if procs else 0))
        h["autosave_runner_count"] = count

        if count >= 1:
            h["autosave_runner_ok"] = True
        else:
            if AUTOSAVE_REQUIRED:
                h["autosave_runner_ok"] = False    # 강제 모드일 때만 문제로 간주
                h.setdefault("warnings", []).append("autosave_runner not running (required)")
            else:
                h["autosave_runner_ok"] = True     # 기본은 INFO로 통과
                _log_info(h, "autosave_runner_info", "not running (treated as normal)")
    except Exception as e:
        h.setdefault("warnings", []).append(f"autosave_runner_check_error: {e}")

def main():
    print("=== VELOS System Integrity Check ===")

    # 각종 무결성 점검
    file_issues = check_file_integrity()
    db_issues = check_db_integrity()
    process_issues = check_process_health()

    all_issues = file_issues + db_issues + process_issues

    # 기본 상태 구조 생성
    status = {
        "check_time": int(time.time()),
        "file_issues": len(file_issues),
        "db_issues": len(db_issues),
        "process_issues": len(process_issues),
        "total_issues": len(all_issues),
        "integrity_ok": len(all_issues) == 0,
        "details": {
            "file_issues": file_issues,
            "db_issues": db_issues,
            "process_issues": process_issues
        }
    }

    # autosave_runner 상태 추가
    check_autosave_runner(status)

    print(json.dumps(status, ensure_ascii=False, indent=2))

    # 헬스 로그 업데이트
    health = jload(HEALTH)
    health.update({
        "system_integrity_last_check": int(time.time()),
        "system_integrity_ok": status["integrity_ok"],
        "system_integrity_issues": all_issues
    })
    jwrite(HEALTH, health)

    if all_issues:
        print(f"[WARNING] System integrity issues found: {len(all_issues)}")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1
    else:
        print("[OK] System integrity check passed")
        return 0

if __name__ == "__main__":
    sys.exit(main())
