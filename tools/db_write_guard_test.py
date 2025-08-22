# =========================================================
# VELOS 운영 철학 선언문
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
import json
import os
import sqlite3
import sys

# 경로 하드코딩 제거, report_paths 모듈 사용
from modules.report_paths import ROOT, P
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VELOS_DB_WRITE_FORBIDDEN", "1")
import app.guards.db_write_guard  # noqa

DB = str(P("data/velos.db"))
OPS = str(P("data/logs/ops_patch_log.jsonl"))


def log(**rec):
    with open(OPS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


con = sqlite3.connect(DB)
cur = con.cursor()
try:
    cur.execute("CREATE TABLE IF NOT EXISTS guard_test (ts TEXT)")
    con.commit()
    print("CREATE_OK")
    log(step="create", result="ok")
except Exception as e:
    print("CREATE_FAIL", type(e).__name__, str(e)[:120])
    log(step="create", result="fail", error=str(e))
    raise

try:
    cur.execute("INSERT INTO guard_test(ts) VALUES ('blocked')")
    con.commit()
    print("UNEXPECTED_INSERT_OK")
    log(step="insert", result="unexpected_ok")
except Exception as e:
    print("EXPECTED_INSERT_BLOCK", type(e).__name__, str(e)[:120])
    log(step="insert", result="blocked", error=str(e)[:120])
