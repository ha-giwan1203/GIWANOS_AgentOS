# [ACTIVE] VELOS 벤치마크 회귀 테스트 (스크립트 복사본)
# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
DB = os.environ.get("VELOS_DB_PATH", r"C:\giwanos\data\velos.db")
OUT_DIR = ROOT / "artifacts" / "bench"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 회귀 기준(느슨하게 시작해서 필요하면 조이세요)
THRESHOLDS = {
    "insert_2000_min_qps": 500,  # 초당 500행 미만이면 실패
    "search_40_max_sec": 0.50,  # 40회 검색에 0.5초 초과면 실패
}


def main():
    ts = time.strftime("%Y%m%d_%H%M%S")
    log_path = OUT_DIR / f"bench_{ts}.log"
    json_path = OUT_DIR / f"bench_{ts}.json"

    # 벤치 실행
    cmd = [sys.executable, str(ROOT / "tests" / "perf" / "benchmark_suite.py")]
    if not os.path.exists(cmd[1]):
        # fallback: scripts 디렉토리에서 실행
        cmd[1] = str(ROOT / "scripts" / "benchmark_suite.py")
    env = os.environ.copy()
    env["VELOS_DB_PATH"] = DB
    print(f"[bench] running: {' '.join(cmd)}")
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    log_path.write_text(p.stdout + "\n\n[stderr]\n" + p.stderr, encoding="utf-8")

    if p.returncode != 0:
        print("[bench] suite failed; see log:", log_path)
        sys.exit(p.returncode)

    # 요약값 파싱(가벼운 정규식)
    out = p.stdout
    data = {"ts": ts, "sanity": {}, "metrics": {}}

    m = re.search(r"\[sanity\]\s*mode=(\w+),\s*sync=(\d+),\s*busy=(\d+)", out)
    if m:
        data["sanity"] = {"mode": m.group(1), "sync": int(m.group(2)), "busy": int(m.group(3))}

    def grab(name: str, pat: str, cast=float):
        mm = re.search(pat, out)
        if mm:
            data["metrics"][name] = cast(mm.group(1))

    # insert 2000
    grab("insert_2000_sec", r"insert_2000:\s*([0-9.]+)s")
    grab("insert_2000_qps", r"insert_2000:\s*[0-9.]+s\s*\(([0-9.]+)/s\)")
    # search 40
    grab("search_40_sec", r"search_40:\s*([0-9.]+)s")

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[bench] wrote {json_path}")

    # 회귀 체크
    fail_msgs = []
    if data["metrics"].get("insert_2000_qps", 1e9) < THRESHOLDS["insert_2000_min_qps"]:
        fail_msgs.append(f"insert_2000_qps<{THRESHOLDS['insert_2000_min_qps']}")
    if data["metrics"].get("search_40_sec", 0.0) > THRESHOLDS["search_40_max_sec"]:
        fail_msgs.append(f"search_40_sec>{THRESHOLDS['search_40_max_sec']}")

    if data["sanity"].get("mode") != "wal" or data["sanity"].get("sync") != 1:
        fail_msgs.append("PRAGMA sanity failed (mode/sync)")

    if fail_msgs:
        print("[bench] REGRESSION:", "; ".join(fail_msgs))
        print("[bench] see:", log_path)
        sys.exit(2)

    print("[bench] PASSED - all thresholds met")


if __name__ == "__main__":
    main()
