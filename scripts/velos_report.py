# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:\giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
from __future__ import annotations

import contextlib
import json
import sqlite3
import time
from datetime import UTC, datetime

from modules.report_paths import ROOT

DB = ROOT / "data" / "velos.db"
HEALTH = ROOT / "data" / "logs" / "system_health.json"
OUTDIR = ROOT / "data" / "reports"
OUTDIR.mkdir(parents=True, exist_ok=True)


def now_utc():
    return datetime.now(UTC)


def ymd():
    return now_utc().astimezone().strftime("%Y%m%d")


def count_since(sec: int) -> int:
    if not DB.exists():
        return 0

    try:
        con = sqlite3.connect(DB)
        t = int(time.time()) - sec
        (n,) = con.execute("select count(*) from messages where created_utc>=?", (t,)).fetchone()
        return n
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        return 0
    finally:
        if "con" in locals():
            con.close()


def main():
    last5 = count_since(5 * 60)
    last60 = count_since(60 * 60)
    last24h = count_since(24 * 60 * 60)
    health = {}
    if HEALTH.exists():
        with contextlib.suppress(Exception):
            health = json.loads(HEALTH.read_text(encoding="utf-8"))

    out = OUTDIR / f"VELOS_Report_{ymd()}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# VELOS Daily Report ({ymd()})\n\n")
        f.write("## Message Counters\n")
        f.write(f"- Last 5 minutes: **{last5}**\n")
        f.write(f"- Last 60 minutes: **{last60}**\n")
        f.write(f"- Last 24 hours: **{last24h}**\n\n")
        f.write("## Health Snapshot\n")
        f.write("```json\n")
        json.dump(health, f, ensure_ascii=False, indent=2)
        f.write("\n```\n")
    print(out)


if __name__ == "__main__":
    main()
