#!/usr/bin/env python3
"""Self-X Layer 1 — invariants 평가 + HEALTH.md 생성.

debate_20260421_133506_3way 만장일치 통과안 구현.
정책: P1 감지만 / P2 SessionStart 1회+캐시 / P3 OS timeout 5s / P4 요약만 incident / P5 디바운스 N=3

Usage:
  python3 .claude/self/diagnose.py            # 평가 → HEALTH.md + JSON 저장 + 1줄 stdout
  python3 .claude/self/diagnose.py --json     # JSON만 stdout
  python3 .claude/self/diagnose.py --force    # 1세션 캐시 무시 강제 재평가
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INVARIANTS_FILE = PROJECT_ROOT / "90_공통기준" / "invariants.yaml"
SELF_DIR = PROJECT_ROOT / ".claude" / "self"
CACHE_FILE = SELF_DIR / "last_diagnosis.json"
HEALTH_FILE = SELF_DIR / "HEALTH.md"
SUMMARY_FILE = SELF_DIR / "summary.txt"  # 1줄 요약 (SessionStart hook이 출력)

OS_TIMEOUT = 5  # P3
DEBOUNCE_N = 3  # P5
SESSION_CACHE_TTL = 1800  # 30분 (1세션 가정)


def load_invariants() -> list[dict]:
    """invariants.yaml 파싱 (외부 yaml 라이브러리 없이)."""
    if not INVARIANTS_FILE.exists():
        return []
    text = INVARIANTS_FILE.read_text(encoding="utf-8")
    invariants = []
    in_list = False
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "invariants:":
            in_list = True
            continue
        if stripped == "deferred:" or stripped.startswith("policy:"):
            in_list = False
            continue
        if not in_list:
            continue
        if stripped.startswith("- name:"):
            if current:
                invariants.append(current)
            current = {"name": stripped.split("name:", 1)[1].strip()}
        elif current and ":" in stripped and not stripped.startswith("#"):
            k, v = stripped.split(":", 1)
            current[k.strip()] = v.strip()
    if current:
        invariants.append(current)
    return invariants


def run_with_timeout(cmd: list[str], timeout: int = OS_TIMEOUT) -> tuple[int, str]:
    """OS timeout 격리 실행 (P3)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=PROJECT_ROOT)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"
    except Exception as e:
        return 1, f"ERROR: {e}"


def file_age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    return (time.time() - path.stat().st_mtime) / 3600


def evaluate_invariant(inv: dict) -> dict:
    """단일 invariant 평가 → {name, status, value, threshold, message}."""
    name = inv["name"]
    severity = inv.get("severity", "warn")
    threshold = inv.get("threshold", "")
    method = inv.get("method", "")
    target = inv.get("target", "")

    result = {
        "name": name,
        "severity": severity,
        "threshold": threshold,
        "status": "OK",
        "value": None,
        "message": "",
    }

    try:
        if method == "file_mtime":
            # target이 glob인 경우 가장 최근 파일
            if "*" in target:
                files = sorted(PROJECT_ROOT.glob(target), key=lambda p: p.stat().st_mtime, reverse=True)
                p = files[0] if files else None
            else:
                p = PROJECT_ROOT / target
            age = file_age_hours(p) if p else None
            if age is None:
                result["status"] = severity.upper()
                result["message"] = f"파일 없음: {target}"
            else:
                result["value"] = f"{age:.1f}h"
                # threshold 파싱
                limit_h = parse_threshold_hours(threshold)
                if limit_h and age > limit_h:
                    result["status"] = severity.upper()
                    result["message"] = f"{age:.1f}h 경과 (임계 {threshold})"
                else:
                    result["message"] = f"last_ok={age:.1f}h 전"

        elif method == "count":
            if target.endswith("incident_ledger.jsonl"):
                p = PROJECT_ROOT / target
                if p.exists():
                    raw = p.read_bytes()
                    unresolved = 0
                    for line in raw.split(b"\r\n"):
                        if not line.strip():
                            continue
                        try:
                            r = json.loads(line)
                            if not r.get("resolved", False):
                                unresolved += 1
                        except Exception:
                            pass
                    result["value"] = unresolved
                    limit = int(threshold)
                    if unresolved > limit:
                        result["status"] = severity.upper()
                        result["message"] = f"{unresolved}건 (임계 {limit})"
                    else:
                        result["message"] = f"{unresolved}건"

        elif method == "smoke_run":
            target_path = target if target.startswith(".") else "./" + target
            rc, out = run_with_timeout(["bash", target_path])
            if rc == 0:
                result["message"] = "ALL PASS"
            else:
                result["status"] = severity.upper()
                result["message"] = f"smoke 실패 rc={rc}"

        elif method == "line_count":
            p = PROJECT_ROOT / target
            if p.exists():
                lines = sum(1 for _ in p.read_text(encoding="utf-8", errors="replace").splitlines())
                result["value"] = lines
                limit = int(threshold)
                if lines > limit:
                    result["status"] = severity.upper()
                    result["message"] = f"{lines}줄 (임계 {limit})"
                else:
                    result["message"] = f"{lines}줄"

        elif method == "git_status":
            rc, out = run_with_timeout(["git", "status", "--porcelain"])
            if rc != 0:
                result["message"] = "git error"
            else:
                changed = [l for l in out.splitlines() if l.strip()]
                if not changed:
                    result["message"] = "clean"
                    result["value"] = 0
                else:
                    # 가장 오래된 변경 파일의 mtime
                    oldest = None
                    for line in changed:
                        parts = line.split(None, 1)
                        if len(parts) >= 2:
                            fpath = PROJECT_ROOT / parts[1].strip('"')
                            if fpath.exists():
                                m = fpath.stat().st_mtime
                                oldest = m if oldest is None else min(oldest, m)
                    age = (time.time() - oldest) / 3600 if oldest else 0
                    result["value"] = f"{len(changed)}개 / 최고령 {age:.1f}h"
                    limit_h = parse_threshold_hours(threshold)
                    if limit_h and age > limit_h:
                        result["status"] = severity.upper()
                        result["message"] = f"미커밋 {len(changed)}건 / {age:.1f}h 경과"
                    else:
                        result["message"] = f"미커밋 {len(changed)}건"

        elif method == "drift_check":
            # settings/README/STATUS hook 수 정합성
            rc, out = run_with_timeout(["python3", "-c", _drift_check_script()])
            if rc == 0 and out.strip().startswith("OK"):
                result["message"] = out.strip()
            else:
                result["status"] = severity.upper()
                result["message"] = f"drift 발견: {out.strip()[:80]}"

        else:
            result["message"] = f"미구현 method: {method}"

    except Exception as e:
        result["status"] = "WARN"
        result["message"] = f"평가 오류: {str(e)[:60]}"

    return result


def parse_threshold_hours(t: str) -> float | None:
    """24h, 5d, business_days_7 등 시간 단위 파싱."""
    t = t.strip()
    if t.endswith("h"):
        return float(t[:-1])
    if t.endswith("d"):
        return float(t[:-1]) * 24
    if t.startswith("business_days_"):
        return float(t.replace("business_days_", "")) * 24 * 1.4  # 영업일 보정
    return None


def _drift_check_script() -> str:
    return """
import json, re
from pathlib import Path
root = Path('.').resolve()
# settings.json hook 수
settings = json.load(open(root/'.claude/settings.json', encoding='utf-8'))
hooks = settings.get('hooks', {})
n_settings = sum(len(v) if isinstance(v, list) else 0 for v in hooks.values())
# 실제 .sh 파일 수
n_files = len(list((root/'.claude/hooks').glob('*.sh')))
# STATUS.md (있으면)
n_status = None
for p in [root/'STATUS.md', root/'90_공통기준/업무관리/STATUS.md']:
    if p.exists():
        m = re.search(r'hooks?\\s*[:=]?\\s*(\\d+)', p.read_text(encoding='utf-8', errors='replace'))
        if m:
            n_status = int(m.group(1))
            break
diffs = []
if n_status is not None and n_status != n_files:
    diffs.append(f'STATUS={n_status} vs files={n_files}')
if abs(n_settings - n_files) > 5:
    diffs.append(f'settings_entries={n_settings} files={n_files}')
print('OK' if not diffs else 'DRIFT: ' + '; '.join(diffs))
"""


def aggregate(results: list[dict]) -> dict:
    ok = sum(1 for r in results if r["status"] == "OK")
    warn = sum(1 for r in results if r["status"] == "WARN")
    crit = sum(1 for r in results if r["status"] == "CRITICAL")
    overall = "OK" if crit == 0 and warn == 0 else ("WARN" if crit == 0 else "CRITICAL")
    return {"ok": ok, "warn": warn, "critical": crit, "overall": overall}


def render_summary(agg: dict) -> str:
    """1줄 요약 (Claude 첫 메시지 의무)."""
    if agg["overall"] == "OK":
        return f"[health] {agg['ok']} OK"
    parts = [f"{agg['ok']} OK"]
    if agg["warn"]:
        parts.append(f"{agg['warn']} WARN")
    if agg["critical"]:
        parts.append(f"{agg['critical']} CRITICAL")
    return f"[health] {' · '.join(parts)}"


def render_health_md(results: list[dict], agg: dict, ts: str) -> str:
    """HEALTH.md 1페이지 대시보드."""
    overall = agg["overall"]
    icon = {"OK": "🟢", "WARN": "🟡", "CRITICAL": "🔴"}.get(overall, "⚪")
    lines = [
        "# System Health",
        "",
        f"**상태**: {icon} {overall} | **평가시각**: {ts}",
        f"**요약**: {render_summary(agg)}",
        "",
        "| Invariant | 상태 | 값 | 비고 |",
        "|-----------|------|-----|------|",
    ]
    for r in results:
        status_icon = {"OK": "🟢", "WARN": "🟡", "CRITICAL": "🔴"}.get(r["status"], "⚪")
        val = r.get("value") or ""
        lines.append(f"| {r['name']} | {status_icon} {r['status']} | {val} | {r['message']} |")
    lines.extend([
        "",
        "---",
        "_정책: Layer 1 감지만 (자동 조치 금지). 출처: debate_20260421_133506_3way (3way 만장일치 pass_ratio=1.0)_",
    ])
    return "\n".join(lines) + "\n"


def is_cache_fresh() -> bool:
    """P2: 1세션 캐시. SESSION_CACHE_TTL 이내면 재계산 금지."""
    if not CACHE_FILE.exists():
        return False
    age = time.time() - CACHE_FILE.stat().st_mtime
    return age < SESSION_CACHE_TTL


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="JSON만 stdout")
    parser.add_argument("--force", action="store_true", help="캐시 무시 강제 재평가")
    parser.add_argument("--summary-only", action="store_true", help="1줄 summary만 stdout")
    args = parser.parse_args()

    SELF_DIR.mkdir(parents=True, exist_ok=True)

    # P2: 캐시 확인
    if not args.force and is_cache_fresh() and CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if args.summary_only:
                print(cached.get("summary", "[health] cached"))
            elif args.json:
                print(json.dumps(cached, ensure_ascii=False))
            else:
                print(cached.get("summary", "[health] cached"))
            return 0
        except Exception:
            pass

    invariants = load_invariants()
    results = [evaluate_invariant(inv) for inv in invariants]
    agg = aggregate(results)
    summary = render_summary(agg)
    ts = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")

    payload = {
        "ts": ts,
        "summary": summary,
        "aggregate": agg,
        "results": results,
    }

    # P4: 요약 1건만 incident에 기록 (실제 incident_ledger 추가는 hook 별도 처리)
    CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    HEALTH_FILE.write_text(render_health_md(results, agg, ts), encoding="utf-8")
    SUMMARY_FILE.write_text(summary + "\n", encoding="utf-8")

    # cp949 호환: stdout 인코딩 강제 (Windows)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if args.summary_only:
        print(summary)
    elif args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(summary)
        if agg["warn"] or agg["critical"]:
            for r in results:
                if r["status"] != "OK":
                    print(f"  - {r['status']}: {r['name']} - {r['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
