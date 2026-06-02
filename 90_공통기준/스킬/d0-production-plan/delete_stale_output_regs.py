"""Delete explicitly approved stale SP3M3 D0 rows by REG_NO.

Standard recovery sequence:
1) DELETE /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do
2) DELETE /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do
3) Re-query ERP + SmartMES and verify the target REG_NO values are gone.

This tool is intentionally narrow. It only allows the 2026-06-02 stale output
rows approved in the task instruction: 337270/RSP3SC0644 and 337271/RSP3SC0590.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import uuid
from pathlib import Path

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
RUN_PY = SCRIPT_DIR / "run.py"
ERP_BASE = "http://erp-dev.samsong.com:19100"
MES_BASE = "http://lmes-dev.samsong.com:19220"
DELETE_RANK_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do"
DELETE_REG_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do"
TARGET_DATE_ISO = "2026-06-02"
TARGET_DATE_MES = "20260602"
LINE_CD = "SP3M3"
EXPECTED_TOTAL_BEFORE = 54
EXPECTED_TOTAL_AFTER = 52
EXPECTED = {
    337270: {"PROD_NO": "RSP3SC0644", "QTY": 125},
    337271: {"PROD_NO": "RSP3SC0590", "QTY": 125},
}
PROTECTED = set(range(336573, 336598)) | set(range(337250, 337256))


def import_run():
    spec = importlib.util.spec_from_file_location("d0_run", RUN_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {RUN_PY}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def intish(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def smartmes_headers(token: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "chnl": "lmes",
        "from": "lmes",
        "to": "LMES",
        "lang": "ko",
        "usrid": "LMES",
        "token": token,
        "tid": uuid.uuid4().hex,
    }


def query_smartmes(token: str) -> list[dict]:
    response = requests.post(
        MES_BASE + "/v2/prdt/schdl/list.api",
        json={"prdtDa": TARGET_DATE_MES, "lineCd": LINE_CD},
        headers=smartmes_headers(token),
        timeout=20,
    )
    response.raise_for_status()
    body = response.json()
    if str(body.get("statusCode")) != "200":
        raise RuntimeError(f"SmartMES list.api failed: {body}")
    rows = body.get("rslt", {}).get("items", []) or []
    rows.sort(key=lambda row: intish(row.get("prdtRank")) or 999999)
    return rows


def actual_reg(row: dict) -> int | None:
    # SmartMES maps ERP REG_NO into this misleading field.
    return intish(row.get("sewmacLabelScanQty")) or intish(row.get("regNo"))


def qty_from_erp(row: dict) -> int:
    return int(row.get("PRDT_QTY") or row.get("ADD_PRDT_QTY") or 0)


def setup_erp_session(d0):
    sess = d0.erp_login_via_http()
    if sess is None:
        raise RuntimeError("ERP OAuth login failed")
    sess.headers.update({
        "ajax": "true",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": d0.D0_URL,
        "Origin": ERP_BASE,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9",
    })
    return sess


def refresh_xsrf(d0, sess) -> str:
    token = d0.refresh_xsrf_from_cookies(sess)
    if not token:
        token = sess.cookies.get("XSRF-TOKEN", "")
        sess.headers["X-XSRF-TOKEN"] = token
    return token


def query_erp_grid(d0, sess) -> list[dict]:
    rows = d0.fetch_tot_grid_via_http(sess, TARGET_DATE_ISO)
    return [row for row in rows if row.get("REG_DT") == TARGET_DATE_ISO]


def erp_target_rows(rows: list[dict]) -> dict[int, dict]:
    found: dict[int, dict] = {}
    for row in rows:
        reg = intish(row.get("REG_NO"))
        if reg in EXPECTED:
            found[reg] = row
    return found


def smartmes_target_rows(rows: list[dict]) -> dict[int, dict]:
    found: dict[int, dict] = {}
    for row in rows:
        reg = actual_reg(row)
        if reg in EXPECTED:
            found[reg] = row
    return found


def assert_preconditions(erp_rows: list[dict], mes_rows: list[dict]) -> None:
    erp_targets = erp_target_rows(erp_rows)
    mes_targets = smartmes_target_rows(mes_rows)
    missing_erp = sorted(set(EXPECTED) - set(erp_targets))
    missing_mes = sorted(set(EXPECTED) - set(mes_targets))
    if missing_erp:
        raise RuntimeError(f"ERP target missing before delete: {missing_erp}")
    if missing_mes:
        raise RuntimeError(f"SmartMES target missing before delete: {missing_mes}")
    if len(mes_rows) != EXPECTED_TOTAL_BEFORE:
        raise RuntimeError(f"SmartMES count before delete {len(mes_rows)} != expected {EXPECTED_TOTAL_BEFORE}")
    for reg, expected in EXPECTED.items():
        erp = erp_targets[reg]
        mes = mes_targets[reg]
        erp_qty = qty_from_erp(erp)
        mes_qty = int(mes.get("planQty") or 0)
        if erp.get("PROD_NO") != expected["PROD_NO"] or erp_qty != expected["QTY"]:
            raise RuntimeError(f"ERP target mismatch REG_NO={reg}: {erp}")
        if mes.get("pno") != expected["PROD_NO"] or mes_qty != expected["QTY"]:
            raise RuntimeError(f"SmartMES target mismatch REG_NO={reg}: {mes}")
    protected_found = sorted(reg for reg in PROTECTED if any(actual_reg(row) == reg for row in mes_rows))
    if len(protected_found) != len(PROTECTED):
        missing = sorted(PROTECTED - set(protected_found))
        raise RuntimeError(f"protected rows missing before delete: {missing}")


def rank_delete_payload(reg: int, pno: str) -> dict:
    return {
        "EXT_PLAN_REG_NO": reg,
        "STD_DA": TARGET_DATE_ISO,
        "PLAN_DA": TARGET_DATE_ISO,
        "PROD_NO": pno,
        "LINE_CD": LINE_CD,
    }


def delete_one(d0, sess, reg: int) -> tuple[dict, dict]:
    expected = EXPECTED[reg]
    refresh_xsrf(d0, sess)
    rank_resp = sess.delete(
        ERP_BASE + DELETE_RANK_URL,
        data=json.dumps(rank_delete_payload(reg, expected["PROD_NO"]), ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "X-XSRF-TOKEN": sess.headers.get("X-XSRF-TOKEN", ""),
        },
        timeout=30,
    )
    rank_body = parse_response(rank_resp)
    print(f"[delete-rank] REG_NO={reg} http={rank_resp.status_code} statusCode={rank_body.get('statusCode')}")
    if rank_resp.status_code != 200 or str(rank_body.get("statusCode")) != "200":
        raise RuntimeError(f"rank DELETE failed REG_NO={reg}: http={rank_resp.status_code} body={rank_resp.text[:500]}")

    refresh_xsrf(d0, sess)
    reg_resp = sess.delete(
        ERP_BASE + DELETE_REG_URL,
        data=json.dumps({"REG_NO": reg}).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "X-XSRF-TOKEN": sess.headers.get("X-XSRF-TOKEN", ""),
        },
        timeout=30,
    )
    reg_body = parse_response(reg_resp)
    print(f"[delete-reg]  REG_NO={reg} http={reg_resp.status_code} statusCode={reg_body.get('statusCode')}")
    if reg_resp.status_code != 200 or str(reg_body.get("statusCode")) != "200":
        raise RuntimeError(f"REG DELETE failed REG_NO={reg}: http={reg_resp.status_code} body={reg_resp.text[:500]}")
    return rank_body, reg_body


def parse_response(response) -> dict:
    try:
        return response.json()
    except Exception:
        return {"raw": response.text[:500]}


def verify_after(d0, sess, mes_token: str, protected_before: dict[int, tuple[int, str, int]]) -> None:
    erp_rows = query_erp_grid(d0, sess)
    mes_rows = query_smartmes(mes_token)
    erp_remaining = erp_target_rows(erp_rows)
    mes_remaining = smartmes_target_rows(mes_rows)
    if erp_remaining:
        raise RuntimeError(f"ERP targets still remain after delete: {sorted(erp_remaining)}")
    if mes_remaining:
        raise RuntimeError(f"SmartMES targets still remain after delete: {sorted(mes_remaining)}")
    if len(mes_rows) != EXPECTED_TOTAL_AFTER:
        raise RuntimeError(f"SmartMES count after delete {len(mes_rows)} != expected {EXPECTED_TOTAL_AFTER}")
    for row in mes_rows:
        reg = actual_reg(row)
        if reg in protected_before:
            old_rank, old_pno, old_qty = protected_before[reg]
            now = (int(row.get("prdtRank") or 0), row.get("pno"), int(row.get("planQty") or 0))
            if now != (old_rank, old_pno, old_qty):
                raise RuntimeError(f"protected row changed REG_NO={reg}: before={protected_before[reg]} after={now}")
    first = mes_rows[0] if mes_rows else {}
    print(f"[verify] ERP targets remaining=0 SmartMES targets remaining=0 SmartMES count={len(mes_rows)}")
    print(f"[verify] rank1={first.get('pno')} REG={actual_reg(first)}")
    print("[verify] first 8 ranks")
    for row in mes_rows[:8]:
        print(
            f"  rank={row.get('prdtRank')} REG={actual_reg(row)} "
            f"pno={row.get('pno')} qty={row.get('planQty')} status={row.get('workStatusCd')}"
        )


def protected_snapshot(mes_rows: list[dict]) -> dict[int, tuple[int, str, int]]:
    out: dict[int, tuple[int, str, int]] = {}
    for row in mes_rows:
        reg = actual_reg(row)
        if reg in PROTECTED:
            out[reg] = (int(row.get("prdtRank") or 0), str(row.get("pno") or ""), int(row.get("planQty") or 0))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="perform DELETE calls")
    args = parser.parse_args()

    d0 = import_run()
    sess = setup_erp_session(d0)
    # Reuse jobsetup-auto dev token if configured there; this is the current
    # proven list.api token for SmartMES schedule reads.
    jobsetup_path = SCRIPT_DIR.parent / "jobsetup-auto" / "run_jobsetup.py"
    spec = importlib.util.spec_from_file_location("jobsetup_run", jobsetup_path)
    jobsetup = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {jobsetup_path}")
    spec.loader.exec_module(jobsetup)
    _, mes_token, token_source = jobsetup.load_env_config("dev")
    print(f"[smartmes-token] source={token_source}")

    erp_rows = query_erp_grid(d0, sess)
    mes_rows = query_smartmes(mes_token)
    assert_preconditions(erp_rows, mes_rows)
    before_protected = protected_snapshot(mes_rows)

    print(f"[precheck] ERP count={len(erp_rows)} SmartMES count={len(mes_rows)} targets={sorted(EXPECTED)}")
    for reg in sorted(EXPECTED):
        erp = erp_target_rows(erp_rows)[reg]
        mes = smartmes_target_rows(mes_rows)[reg]
        print(
            f"  REG_NO={reg} PROD_NO={EXPECTED[reg]['PROD_NO']} "
            f"ERP_QTY={qty_from_erp(erp)} MES_rank={mes.get('prdtRank')} MES_QTY={mes.get('planQty')}"
        )

    if not args.execute:
        print("[done] dry-run only; no DELETE called")
        return 0

    for reg in sorted(EXPECTED):
        delete_one(d0, sess, reg)
    verify_after(d0, sess, mes_token, before_protected)
    print("[done] stale output rows deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
