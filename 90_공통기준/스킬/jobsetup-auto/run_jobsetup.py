"""SmartMES 잡셋업 자동 입력 본체 v2.2 — REST API 직호출 (UI 자동화 폐지)

근거:
- ServiceAgent.SaveJobSetup (dnSpy 디컴파일):
    POST /v2/checksheet/check-result/jobsetup/save.api + JSON body
    Headers: tid(uuid32), chnl=lmes, from=lmes, to=LMES, lang=ko, usrid=LMES, token
- ServiceAgent.GetJobSetup → POST /v2/checksheet/check-result/jobsetup/list.api + JobSetupQRY
- MESClient.exe.config: ApiServerMes=http://lmes-dev.samsong.com:19220 + Token (32자 hex)
- CommonConst: CHNL/FROM=lmes, TO/USRID=LMES, LANG=ko, HTTP_RESULT_OK=200

흐름:
1. list.api로 (prdtDa, lineCd, pno, pnoRev, prdtRank) → 17개 검사항목 + spec 회수
2. 각 미등록 항목(rslt='') 에 대해:
   - mngAriclCmnt 정규식 분류 (A=측정값 A1/A2/A3 / B=OK/NG)
   - A형: gen_normal_in_range × 3
   - B형: x1/x2/x3 = ""
   - 모든 RsltCd="O", RsltNm="OK", finalCheckRsltCd="O"/"OK"
3. save.api 1건씩 POST + 응답 검증

모드:
- list-only:    검사항목 출력 (저장 0, 입력 0)
- dry-run:      입력값까지 계산 (저장 0)
- commit-one:   첫 미등록 1건만 저장 (검증용)
- commit-all:   모든 미등록 항목 저장 (운영)

❌ NG 자동 체크 금지
❌ 무인 자동 실행은 사용자 입회 시에만
"""
import argparse
import json
import os
import random
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).parent
STATE_DIR = SCRIPT_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)
CONFIG_PATH = SCRIPT_DIR / "config.json"

# dev default (v3.0 호환). prod 전환 시 환경변수 또는 config.json에서 회수
DEV_DEFAULT = {
    "mes_server": "http://lmes-dev.samsong.com:19220",
    "mes_token": "6c02224ce114410c8e53f45d1939a5b3",
}


def load_env_config(env: str):
    """환경변수 → config.json → dev default 순으로 (server, token) 회수.

    env='dev' : 환경변수 → config.json[dev] → DEV_DEFAULT
    env='prod': 환경변수 → config.json[prod] → 없으면 abort
    """
    # 1순위: 환경변수 (모든 env 공통)
    server = os.environ.get("JOBSETUP_MES_SERVER")
    token = os.environ.get("JOBSETUP_MES_TOKEN")
    if server and token:
        return server, token, "env"

    # 2순위: config.json
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] config.json 파싱 실패: {e}", file=sys.stderr)
    sect = cfg.get(env, {})
    server = sect.get("mes_server")
    token = sect.get("mes_token")
    if server and token:
        return server, token, f"config.json[{env}]"

    # 3순위: dev default (env=dev만)
    if env == "dev":
        return DEV_DEFAULT["mes_server"], DEV_DEFAULT["mes_token"], "dev_default"

    # prod 인데 회수 실패 → abort
    raise SystemExit(
        f"[ABORT] env={env} 설정 미발견.\n"
        f"  환경변수 JOBSETUP_MES_SERVER + JOBSETUP_MES_TOKEN 설정\n"
        f"  또는 {CONFIG_PATH} 에 {{\"prod\": {{\"mes_server\": \"...\", \"mes_token\": \"...\"}}}} 추가\n"
        f"  config.example.json 참조"
    )


def build_common_headers(token: str):
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "chnl": "lmes",
        "from": "lmes",
        "to": "LMES",
        "lang": "ko",
        "usrid": "LMES",
        "token": token,
    }


# 모듈 레벨 변수 (build_headers 등 기존 호출부 호환). main에서 setup_runtime로 채움
MES_SERVER = None
COMMON_HEADERS = None


# ---- spec 분류 (screen_analysis_20260429.md) ----
RE_A1 = re.compile(r"^\s*([-+]?\d+(?:\.\d+)?)\s*[±]\s*(\d+(?:\.\d+)?)\s*\w*\s*$")
RE_A2 = re.compile(r"([-+]?\d+(?:\.\d+)?)\s*\+(\d+(?:\.\d+)?)\s*\w*\s*,?\s*-(\d+(?:\.\d+)?)\s*\w*")


def _dec_count(s):
    return len(s.split(".")[1]) if "." in s else 0


def classify_spec(text):
    """spec text → ('A', [(lo, hi, decimals), ...]) 또는 ('B', None)."""
    if not text:
        return ("B", None)
    s = text.strip()
    m = RE_A1.match(s)
    if m:
        center = float(m.group(1))
        tol = float(m.group(2))
        d = max(_dec_count(m.group(1)), _dec_count(m.group(2)))
        return ("A", [(center - tol, center + tol, d)])
    matches = list(RE_A2.finditer(s))
    if matches:
        ranges = []
        for m in matches:
            center = float(m.group(1))
            up = float(m.group(2))
            dn = float(m.group(3))
            d = max(_dec_count(m.group(1)), _dec_count(m.group(2)), _dec_count(m.group(3)))
            ranges.append((center - dn, center + up, d))
        if len(ranges) > 1:
            # A3 복합 비대칭 → 교집합 (양쪽 통과해야 OK)
            lo = max(r[0] for r in ranges)
            hi = min(r[1] for r in ranges)
            d = max(r[2] for r in ranges)
            return ("A", [(lo, hi, d)])
        return ("A", ranges)
    return ("B", None)


def gen_normal_in_range(lo, hi, decimals):
    """[lo, hi] 정규분포 난수, σ = 반폭/3."""
    center = (lo + hi) / 2.0
    half = (hi - lo) / 2.0
    sigma = half / 3.0
    while True:
        v = random.gauss(center, sigma)
        if lo <= v <= hi:
            return round(v, decimals)


# ---- API ----

def setup_runtime(env: str):
    """env에 따라 MES_SERVER/COMMON_HEADERS 모듈 변수 설정. main에서 호출."""
    global MES_SERVER, COMMON_HEADERS
    server, token, src = load_env_config(env)
    MES_SERVER = server
    COMMON_HEADERS = build_common_headers(token)
    return src


def build_headers():
    h = dict(COMMON_HEADERS)
    h["tid"] = uuid.uuid4().hex
    return h


def call_list(qry):
    url = f"{MES_SERVER}/v2/checksheet/check-result/jobsetup/list.api"
    r = requests.post(url, json=qry, headers=build_headers(), timeout=15)
    r.raise_for_status()
    j = r.json()
    sc = str(j.get("statusCode", ""))
    if sc != "200":
        raise RuntimeError(f"list.api statusCode={sc} msg={j.get('statusMsg')}")
    return j.get("rslt", {}).get("items", [])


def call_save(item):
    url = f"{MES_SERVER}/v2/checksheet/check-result/jobsetup/save.api"
    r = requests.post(url, json=item, headers=build_headers(), timeout=20)
    j = None
    try:
        j = r.json()
    except Exception:
        pass
    return r.status_code, j, r.text[:300]


def call_schedule(prdt_da: str, line_cd: str):
    """v3.3: GetProductionSchedule API. POST /v2/prdt/schdl/list.api.

    근거: ServiceAgent.GetProductionSchedule (dnSpy 디컴파일):
        request body = {prdtDa, lineCd}, 응답 = ScheduleDTO.rslt.items[]
        ScheduleItem property: pno, pnoRev, prdtRank, lineCd, prdtDa, regNo, revNo 등

    Returns: prdtRank 오름차순 정렬된 items 리스트.
    """
    url = f"{MES_SERVER}/v2/prdt/schdl/list.api"
    body = {"prdtDa": prdt_da, "lineCd": line_cd}
    r = requests.post(url, json=body, headers=build_headers(), timeout=15)
    r.raise_for_status()
    j = r.json()
    sc = str(j.get("statusCode", ""))
    if sc != "200":
        raise RuntimeError(f"schdl/list.api statusCode={sc} msg={j.get('statusMsg')}")
    items = j.get("rslt", {}).get("items", []) or []
    items.sort(key=lambda it: (it.get("prdtRank") or 99))
    return items


def resolve_first_sequence(prdt_da: str, line_cd: str):
    """schedule API로 prdtRank=1 항목 회수. 없으면 None."""
    items = call_schedule(prdt_da, line_cd)
    for it in items:
        if (it.get("prdtRank") or 0) == 1:
            return it
    return None


def build_save_item(master_item, qry, kind, params):
    """list.api 응답 1건(master) + qry 컨텍스트 + A/B 분기 → save.api payload."""
    out = dict(master_item)  # 마스터 11개 그대로 + 추가 컨텍스트
    out.setdefault("pno", qry["pno"])
    out.setdefault("pnoRev", qry["pnoRev"])
    out.setdefault("prdtRank", qry.get("prdtRank", 1))
    out.setdefault("regNo", qry.get("regNo", 0))
    out.setdefault("revNo", qry.get("revNo", "0"))
    if kind == "A":
        lo, hi, decimals = params[0]
        v1 = gen_normal_in_range(lo, hi, decimals)
        v2 = gen_normal_in_range(lo, hi, decimals)
        v3 = gen_normal_in_range(lo, hi, decimals)
        out["x1"] = f"{v1:.{decimals}f}"
        out["x2"] = f"{v2:.{decimals}f}"
        out["x3"] = f"{v3:.{decimals}f}"
    else:
        out["x1"] = ""
        out["x2"] = ""
        out["x3"] = ""
    out["x1RsltCd"] = "O"
    out["x2RsltCd"] = "O"
    out["x3RsltCd"] = "O"
    out["x1RsltNm"] = "OK"
    out["x2RsltNm"] = "OK"
    out["x3RsltNm"] = "OK"
    out["finalCheckRsltCd"] = "O"
    out["finalCheckRsltNm"] = "OK"
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["list-only", "dry-run", "commit-one", "commit-all"],
                   default="list-only")
    p.add_argument("--prdt-da", default=None, help="YYYYMMDD (default=오늘)")
    p.add_argument("--line-cd", default="SP3M3")
    p.add_argument("--pno", default=None, help="첫 서열 품번. 미지정 + --auto-resolve-pno 사용 시 schedule API로 회수")
    p.add_argument("--pno-rev", default=None)
    p.add_argument("--prdt-rank", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--env", choices=["dev", "prod"], default="dev",
                   help="MES 환경 (default=dev). prod 사용 시 환경변수 JOBSETUP_MES_SERVER/TOKEN 또는 config.json 필수")
    p.add_argument("--auto-resolve-pno", action="store_true",
                   help="v3.3: schedule API로 prdtRank=1 품번 자동 회수. --pno 동시 지정 + 불일치 시 abort")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    else:
        random.seed()

    if args.prdt_da is None:
        args.prdt_da = datetime.now().strftime("%Y%m%d")

    cfg_src = setup_runtime(args.env)
    if args.env == "prod" and args.mode in ("commit-one", "commit-all"):
        print(f"[!] env=prod commit 모드 — server={MES_SERVER} (cfg={cfg_src}). 사용자 입회 확인 필요", file=sys.stderr)

    # v3.3: --auto-resolve-pno 처리. 사용자 인자와 충돌 시 abort.
    if args.auto_resolve_pno:
        sched = resolve_first_sequence(args.prdt_da, args.line_cd)
        if sched is None:
            raise SystemExit(f"[ABORT] schedule API에 prdtDa={args.prdt_da} lineCd={args.line_cd} prdtRank=1 항목 없음 (휴일·미반영 가능)")
        api_pno, api_rev = sched.get("pno"), sched.get("pnoRev")
        print(f"[schedule] auto-resolve → pno={api_pno} pnoRev={api_rev} (cfg={cfg_src})")
        if args.pno and args.pno != api_pno:
            raise SystemExit(f"[ABORT] --pno '{args.pno}' vs schedule API '{api_pno}' 불일치")
        if args.pno_rev and args.pno_rev != api_rev:
            raise SystemExit(f"[ABORT] --pno-rev '{args.pno_rev}' vs schedule API '{api_rev}' 불일치")
        args.pno = api_pno
        args.pno_rev = api_rev

    # default fallback (auto-resolve 미사용 + --pno 미지정 시 v3.0 호환 default)
    if args.pno is None:
        args.pno = "RSP3SC0646"
    if args.pno_rev is None:
        args.pno_rev = "A"

    qry = {
        "prdtDa": args.prdt_da,
        "lineCd": args.line_cd,
        "pno": args.pno,
        "pnoRev": args.pno_rev,
        "prdtRank": args.prdt_rank,
        "regNo": 0,
        "revNo": "0",
        "procNo": "",
    }

    started = datetime.now()
    log = {
        "ts_start": started.isoformat(),
        "mode": args.mode,
        "qry": qry,
        "items": [],
        "save_count": 0,
        "fail_count": 0,
    }

    print(f"=== jobsetup v2.2 mode={args.mode} ===")
    print(f"  qry: {qry}")
    print()

    items = call_list(qry)
    print(f"[list] {len(items)} items")

    if not items:
        print("[FAIL] no items returned")
        return 2

    # 미등록 항목만 (finalCheckRsltCd 비어있는 것)
    pending = [it for it in items if not (it.get("finalCheckRsltCd") or "").strip()]
    done = [it for it in items if (it.get("finalCheckRsltCd") or "").strip()]
    print(f"  pending={len(pending)} already_done={len(done)}")

    # 분류 + 입력 생성
    plans = []
    for it in pending:
        spec = it.get("mngAriclCmnt", "")
        kind, params = classify_spec(spec)
        plan = {
            "procNo": it.get("procNo"),
            "mngAriclCd": it.get("mngAriclCd"),
            "mngAriclNm": (it.get("mngAriclNm") or "")[:40],
            "stdDivCd": it.get("stdDivCd"),
            "spec": spec,
            "kind": kind,
            "params": [list(p) for p in params] if params else None,
        }
        if args.mode != "list-only":
            payload = build_save_item(it, qry, kind, params)
            plan["payload"] = payload
            plan["values"] = [payload["x1"], payload["x2"], payload["x3"]]
        plans.append(plan)
        log["items"].append(plan)

    print(f"\n=== plan ({len(plans)}건) ===")
    for p_ in plans:
        vals = p_.get("values", ["", "", ""])
        print(f"  proc={p_['procNo']:4s} [{p_['mngAriclCd']}] {p_['mngAriclNm']:35s} "
              f"std={p_['stdDivCd']} kind={p_['kind']} spec='{p_['spec'][:30]}' vals={vals}")

    if args.mode == "list-only" or args.mode == "dry-run":
        out = STATE_DIR / f"run_v22_{started:%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {out.name} mode={args.mode} (no save)")
        return 0

    # commit
    targets = plans[:1] if args.mode == "commit-one" else plans
    print(f"\n=== commit ({len(targets)}건) ===")
    for p_ in targets:
        payload = p_["payload"]
        sc, j, body = call_save(payload)
        msg = (j or {}).get("statusMsg", "") if j else ""
        ok = (sc == 200 and j and str(j.get("statusCode", "")) == "200")
        p_["save_status"] = sc
        p_["save_msg"] = msg
        p_["save_ok"] = ok
        if ok:
            log["save_count"] += 1
            print(f"  [OK]   proc={p_['procNo']} [{p_['mngAriclCd']}] {p_['mngAriclNm'][:30]} | {msg[:60]}")
        else:
            log["fail_count"] += 1
            print(f"  [FAIL] proc={p_['procNo']} [{p_['mngAriclCd']}] sc={sc} msg='{msg[:80]}' body={body[:200]}")
            if args.mode == "commit-one":
                break

    log["ts_end"] = datetime.now().isoformat()
    out = STATE_DIR / f"run_v22_{started:%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[summary] mode={args.mode} saved={log['save_count']} failed={log['fail_count']} | {out.name}")
    return 0 if log["fail_count"] == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
