# VELOS 운영 철학 선언문: 파일명 고정, 자가 검증 필수, 결과 기록, 경로/구조 불변, 실패 시 안전 복구와 알림.
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "C:\giwanos"

    def get_data_path(*parts):
        return os.path.join("C:\giwanos", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("C:\giwanos", "configs", *parts)

    def get_db_path():
        return "C:\giwanos/data/memory/velos.db"


ROOT = get_velos_root() if "get_velos_root" in locals() else "C:\giwanos"
HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")


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


def check_memory_data_integrity():
    """메모리 데이터 무결성 점검"""
    issues = []

    # memory_buffer.jsonl 점검
    buffer_path = os.path.join(ROOT, "data", "memory", "memory_buffer.jsonl")
    if os.path.exists(buffer_path):
        try:
            with open(buffer_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.strip():
                        try:
                            json.loads(line.strip())
                        except json.JSONDecodeError:
                            issues.append(f"json_invalid:memory_buffer.jsonl:line_{i+1}")
        except Exception as e:
            issues.append(f"read_error:memory_buffer.jsonl - {e}")
    else:
        issues.append("missing:memory_buffer.jsonl")

    # learning_memory.json 점검
    json_path = os.path.join(ROOT, "data", "memory", "learning_memory.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    issues.append("format_error:learning_memory.json - not a list")
        except json.JSONDecodeError as e:
            issues.append(f"json_invalid:learning_memory.json - {e}")
        except Exception as e:
            issues.append(f"read_error:learning_memory.json - {e}")
    else:
        issues.append("missing:learning_memory.json")

    return issues


def check_database_data_integrity():
    """데이터베이스 데이터 무결성 점검"""
    issues = []

    # velos.db 점검 (올바른 DB 파일)
    db_path = os.path.join(ROOT, "data", "memory", "velos.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            cur = conn.cursor()

            # 테이블 존재 확인
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory'")
            if not cur.fetchone():
                issues.append("missing_table:memory")
            else:
                # 스키마 점검
                cur.execute("PRAGMA table_info(memory)")
                columns = {row[1] for row in cur.fetchall()}
                required_columns = {"id", "ts", "role", "insight", "raw", "tags"}
                missing_columns = required_columns - columns
                if missing_columns:
                    issues.append(f"missing_columns:memory - {missing_columns}")

                # 데이터 샘플 점검
                cur.execute("SELECT ts, role, insight, raw, tags FROM memory LIMIT 5")
                for row in cur.fetchall():
                    ts, role, insight, raw, tags = row
                    if not isinstance(ts, int) or ts <= 0:
                        issues.append("invalid_ts:memory")
                    if not role or not isinstance(role, str):
                        issues.append("invalid_role:memory")
                    if not insight or not isinstance(insight, str):
                        issues.append("invalid_insight:memory")
                    try:
                        if raw:
                            json.loads(raw)
                        if tags:
                            json.loads(tags)
                    except json.JSONDecodeError:
                        issues.append("invalid_json:memory")

            conn.close()
        except Exception as e:
            issues.append(f"db_error:velos.db - {e}")
    else:
        issues.append("missing:velos.db")

    return issues


def check_report_data_integrity():
    """보고서 데이터 무결성 점검"""
    issues = []

    reports_dir = os.path.join(ROOT, "data", "reports")
    if os.path.exists(reports_dir):
        # 최근 보고서 파일들 점검
        try:
            report_files = []
            for root, dirs, files in os.walk(reports_dir):
                for file in files:
                    if file.endswith((".md", ".json", ".pdf")):
                        report_files.append(os.path.join(root, file))

            # 최근 10개 파일만 점검
            recent_files = sorted(report_files, key=os.path.getmtime, reverse=True)[:10]

            for file_path in recent_files:
                try:
                    if file_path.endswith(".json"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            json.load(f)
                    elif file_path.endswith(".md"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if len(content) < 10:  # 너무 작은 파일
                                issues.append(f"empty_report:{os.path.basename(file_path)}")
                except Exception as e:
                    issues.append(f"corrupt_report:{os.path.basename(file_path)} - {e}")
        except Exception as e:
            issues.append(f"report_scan_error - {e}")
    else:
        issues.append("missing:data/reports")

    return issues


def main():
    print("=== VELOS Data Integrity Check ===")

    # 각종 데이터 무결성 점검
    memory_issues = check_memory_data_integrity()
    db_issues = check_database_data_integrity()
    report_issues = check_report_data_integrity()

    all_issues = memory_issues + db_issues + report_issues

    status = {
        "check_time": int(time.time()),
        "memory_issues": len(memory_issues),
        "db_issues": len(db_issues),
        "report_issues": len(report_issues),
        "total_issues": len(all_issues),
        "data_integrity_ok": len(all_issues) == 0,
        "details": {
            "memory_issues": memory_issues,
            "db_issues": db_issues,
            "report_issues": report_issues,
        },
    }

    print(json.dumps(status, ensure_ascii=False, indent=2))

    # 헬스 로그 업데이트
    health = jload(HEALTH)
    health.update(
        {
            "data_integrity_last_check": int(time.time()),
            "data_integrity_ok": status["data_integrity_ok"],
            "data_integrity_issues": all_issues,
        }
    )
    jwrite(HEALTH, health)

    if all_issues:
        print(f"[WARNING] Data integrity issues found: {len(all_issues)}")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1
    else:
        print("[OK] Data integrity check passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
