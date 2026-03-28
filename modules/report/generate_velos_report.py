# [ACTIVE] VELOS 운영 철학 선언문
# =========================================================
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Use centralized path manager
from modules.core.path_manager import (
    get_velos_root,
    get_data_path,
    get_snapshots_path,
)

ROOT = get_velos_root()
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


class SafeDict(dict):
    """dict that returns empty string for missing keys to avoid KeyError on format_map"""
    def __missing__(self, key):
        return ""


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _list_recent_snapshots(limit: int = 5) -> List[str]:
    """Efficiently list most recent snapshot files.
    - Honors custom VELOS_SNAP_DIR (via get_snapshots_path)
    - Uses os.scandir to avoid loading all entries into memory
    - Sorts by modified time desc and returns top N
    """
    try:
        snap_dir = get_snapshots_path()
        if not snap_dir or not os.path.isdir(snap_dir):
            # fallback to data/snapshots inside root
            snap_dir = get_data_path("snapshots")
        if not os.path.isdir(snap_dir):
            return []

        items = []
        with os.scandir(snap_dir) as it:
            for entry in it:
                # Limit file system traversal for speed
                if not entry.is_file():
                    continue
                name = entry.name
                if name.startswith("snapshot_") and (name.endswith(".zip") or name.endswith(".json")):
                    try:
                        stat = entry.stat()
                        items.append((stat.st_mtime, name))
                    except Exception:
                        continue
        items.sort(key=lambda x: x[0], reverse=True)
        return [name for _, name in items[:limit]]
    except Exception:
        return []


def get_system_stats() -> Dict[str, Any]:
    """시스템 통계 수집 (경량·안전)
    - MemoryAdapter.get_stats()
    - data/logs/system_health.json
    - 최근 스냅샷 5개
    """
    stats: Dict[str, Any] = {}

    # 메모리 통계 (에러 무시)
    try:
        from modules.core.memory_adapter import MemoryAdapter
        adapter = MemoryAdapter()
        stats["memory_stats"] = adapter.get_stats()
    except Exception as e:
        stats["memory_stats"] = {"error": str(e)}

    # 헬스 로그 읽기
    health_path = get_data_path("logs", "system_health.json")
    stats["health_log"] = _read_json(health_path) if os.path.exists(health_path) else {}

    # 최근 스냅샷 (빠른 방식)
    stats["recent_snapshots"] = _list_recent_snapshots(limit=5)

    # 생성 시각
    stats["timestamp"] = datetime.now().isoformat(timespec="seconds")

    return stats


def load_template(report_type: str) -> str:
    """Load a template text for the given report type.
    Fallback order: {type}.md -> system.md -> built-in minimal
    """
    rt = (report_type or "system").strip().lower()
    candidates = [TEMPLATE_DIR / f"{rt}.md", TEMPLATE_DIR / "system.md"]
    for p in candidates:
        try:
            if p.is_file():
                return p.read_text(encoding="utf-8")
        except Exception:
            continue
    # Built-in minimal fallback
    return (
        "# VELOS Report ({timestamp})\n\n"
        "## Summary\n"
        "- Items in buffer: {buffer_size}\n"
        "- DB records: {db_records}\n"
        "- Last sync: {last_sync}\n"
    )


def build_context(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten and normalize stats into template context."""
    mem = stats.get("memory_stats") or {}
    health = stats.get("health_log") or {}

    # memory errors
    memory_error = mem.get("error") if isinstance(mem, dict) else None

    # memory numbers (safe)
    buffer_size = mem.get("buffer_size", 0) if isinstance(mem, dict) else 0
    db_records = mem.get("db_records", 0) if isinstance(mem, dict) else 0
    json_records = mem.get("json_records", 0) if isinstance(mem, dict) else 0
    last_sync = mem.get("last_sync") if isinstance(mem, dict) else None

    # health flags (various schemas allowed)
    system_integrity_ok = None
    data_integrity_ok = None
    health_error = None

    if isinstance(health, dict):
        # flat keys
        system_integrity_ok = health.get("system_integrity_ok")
        data_integrity_ok = health.get("data_integrity_ok")
        if health.get("error"):
            health_error = health.get("error")
        # nested common schema support
        sys_int = health.get("system_integrity") if isinstance(health.get("system_integrity"), dict) else None
        if sys_int and system_integrity_ok is None:
            system_integrity_ok = sys_int.get("integrity_ok")
        data_int = health.get("data_integrity") if isinstance(health.get("data_integrity"), dict) else None
        if data_int and data_integrity_ok is None:
            data_integrity_ok = data_int.get("data_integrity_ok")

    # snapshots bullets
    snaps = stats.get("recent_snapshots") or []
    recent_snapshots_bullets = "\n".join(f"- {s}" for s in snaps) if snaps else "- No snapshots found"

    return {
        "timestamp": stats.get("timestamp", datetime.now().isoformat(timespec="seconds")),
        "buffer_size": buffer_size,
        "db_records": db_records,
        "json_records": json_records,
        "last_sync": last_sync or "",
        "memory_error": memory_error or "",
        "system_integrity_ok": system_integrity_ok if system_integrity_ok is not None else "Unknown",
        "data_integrity_ok": data_integrity_ok if data_integrity_ok is not None else "Unknown",
        "health_error": health_error or "",
        "recent_snapshots_bullets": recent_snapshots_bullets,
        # convenience
        "root": ROOT,
    }


def render_template(template_text: str, context: Dict[str, Any]) -> str:
    return template_text.format_map(SafeDict(**context))


def generate_markdown_report(stats: Dict[str, Any], report_type: str = "system") -> str:
    tmpl = load_template(report_type)
    ctx = build_context(stats)
    return render_template(tmpl, ctx)


def save_report(report_content: str, report_type: str = "system") -> Dict[str, Any]:
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"velos_{report_type}_report_{ts}.md"
        report_path = get_data_path("reports", report_filename)
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        return {"success": True, "report_path": report_path, "filename": report_filename}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="VELOS Report Generator (template-based)")
    parser.add_argument("--type", dest="report_type", default="system", choices=["system", "health", "memory"], help="Report type")
    parser.add_argument("--fast", action="store_true", help="Skip heavy probes if any (kept lightweight by default)")
    args = parser.parse_args()

    print("=== VELOS Report Generator ===")
    print(f"Type: {args.report_type}")

    # 시스템 통계 수집
    stats = get_system_stats()

    # 보고서 생성
    content = generate_markdown_report(stats, report_type=args.report_type)

    # 보고서 저장
    result = save_report(content, report_type=args.report_type)

    if result.get("success"):
        print("✅ Report generated successfully")
        print(f"📁 Location: {result['report_path']}")
        print(f"📄 Filename: {result['filename']}")
        print(json.dumps({"success": True, **result, "stats": stats}, ensure_ascii=False, indent=2))
        sys.exit(0)
    else:
        print(f"❌ Report generation failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
