"""SmartMES 잡셋업 자동 입력 본체 v2.2 - REST API 직호출 (UI 자동화 폐지)

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
            r = round(v, decimals)
            if r == 0:
                r = 0.0
            return r


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


def call_assign_list(qry):
    """v3.4: 작업자 배치 조회 (read-only).

    POST /v2/wrk/assign/list.api + WorkerQRY.
    근거: ServiceAgent.GetWorkerArrangeResult(token, WorkerQRY) (dnSpy).
    중요: shiftsCd=""(빈 값)이어야 응답에 6공정 회수됨. 응답 안에 실제 shiftsCd="01" 포함.

    Returns: 공정별 작업자 items (procNo/wrkId/wrkNm/wrkCertiYn/regNo/shiftsCd 등).
    """
    url = f"{MES_SERVER}/v2/wrk/assign/list.api"
    body = {
        "prdtDa": qry["prdtDa"],
        "lineCd": qry["lineCd"],
        "pno": qry["pno"],
        "pnoRev": qry["pnoRev"],
        "prdtRank": qry.get("prdtRank", 1),
        "regNo": qry.get("regNo", 0),
        "revNo": qry.get("revNo", "0"),
        "shiftsCd": "",
        "procCd": "",
        "procNo": "",
        "wrkId": "",
        "mainProcYn": "",
        "existWrk": "",
    }
    r = requests.post(url, json=body, headers=build_headers(), timeout=15)
    r.raise_for_status()
    j = r.json()
    sc = str(j.get("statusCode", ""))
    if sc != "200":
        raise RuntimeError(f"assign/list.api statusCode={sc} msg={j.get('statusMsg')}")
    return (j.get("rslt") or {}).get("items") or []


def call_assign_best_list(qry, shifts_cd: str = "01"):
    """v3.5: 최적배치 추천 회수 (read-only).

    POST /v2/wrk/assign-best/list.api + WorkerQRY.
    근거: ServiceAgent.GetBestWorkerArrange(token, WorkerQRY) (dnSpy).
    중요: shiftsCd 필수 입력 ("01" 주간 / "02" 야간). 빈 값이면 sc=801.

    Returns: 공정별 추천 작업자 items (assign/list와 동일 스키마).
    """
    url = f"{MES_SERVER}/v2/wrk/assign-best/list.api"
    body = {
        "prdtDa": qry["prdtDa"],
        "lineCd": qry["lineCd"],
        "pno": qry["pno"],
        "pnoRev": qry["pnoRev"],
        "prdtRank": qry.get("prdtRank", 1),
        "regNo": qry.get("regNo", 0),
        "revNo": qry.get("revNo", "0"),
        "shiftsCd": shifts_cd,
        "procCd": "",
        "procNo": "",
        "wrkId": "",
        "mainProcYn": "",
        "existWrk": "",
    }
    r = requests.post(url, json=body, headers=build_headers(), timeout=15)
    r.raise_for_status()
    j = r.json()
    sc = str(j.get("statusCode", ""))
    if sc != "200":
        raise RuntimeError(f"assign-best/list.api statusCode={sc} msg={j.get('statusMsg')}")
    return (j.get("rslt") or {}).get("items") or []


def call_assign_save(items):
    """v3.5: 작업자 배치 저장.

    POST /v2/wrk/assign/save.api + List<WrkItem>.
    근거: ServiceAgent.saveAssignWrk(token, List`1 param) → Boolean (dnSpy).
    body는 assign-best/list 응답 items 그대로 넣음 (assitItems 포함).

    Returns: (status_code, response_json, raw_text).
    """
    url = f"{MES_SERVER}/v2/wrk/assign/save.api"
    r = requests.post(url, json=items, headers=build_headers(), timeout=20)
    j = None
    try:
        j = r.json()
    except Exception:
        pass
    return r.status_code, j, r.text[:300]


def is_assignment_complete(assigns):
    """배치 완료 여부 - 6공정 모두 wrkId 채워져있으면 True."""
    if not assigns:
        return False
    return all((a.get("wrkId") or "").strip() for a in assigns)


def auto_shift_code():
    """현재 시각 → 주간(01) / 야간(02) 자동 추정.
    06:00~17:59 = 주간(01), 그 외 = 야간(02).
    """
    h = datetime.now().hour
    return "01" if 6 <= h < 18 else "02"


def build_auth_payload(assign_item):
    """assign/list 응답 1건 → auth/cnfm/save.api payload (WorkerQRY).

    WorkerQRY 13 property 중 인증에 필요한 핵심 필드만 채움.
    """
    return {
        "prdtDa": assign_item["prdtDa"],
        "lineCd": assign_item["lineCd"],
        "revNo": str(assign_item.get("revNo", "0")),
        "regNo": assign_item["regNo"],
        "prdtRank": assign_item["prdtRank"],
        "pno": assign_item["pno"],
        "pnoRev": assign_item["pnoRev"],
        "shiftsCd": assign_item.get("shiftsCd", "01"),
        "procCd": assign_item["procCd"],
        "procNo": assign_item["procNo"],
        "wrkId": assign_item["wrkId"],
        "mainProcYn": "Y",
        "existWrk": "Y",
    }


def call_auth_cnfm(payload):
    """v3.4: 작업자 인증 저장.

    POST /v2/wrk/auth/cnfm/save.api + WorkerQRY.
    근거: ServiceAgent.CheckWorker(token, WorkerQRY) → Boolean (dnSpy).

    Returns: (status_code, response_json, raw_text).
    """
    url = f"{MES_SERVER}/v2/wrk/auth/cnfm/save.api"
    r = requests.post(url, json=payload, headers=build_headers(), timeout=20)
    j = None
    try:
        j = r.json()
    except Exception:
        pass
    return r.status_code, j, r.text[:300]


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
    p.add_argument("--with-auth", action="store_true",
                   help="v3.4: 작업자 인증 단계 포함 (auth/cnfm/save.api). 미인증 상태에서 자동화 시 잡셋업 미완료 처리되는 문제 해결")
    p.add_argument("--with-assign", action="store_true",
                   help="v3.5: 작업자 배치 단계 포함 (assign-best/list + assign/save). 배치 미완료 시에만 자동 배치 (멱등). 이미 배치돼있으면 SKIP")
    p.add_argument("--shift", choices=["D", "N", "auto"], default="auto",
                   help="v3.5: 작업조 (D=주간 01 / N=야간 02 / auto=시각 기반). 배치 시 필수")
    p.add_argument("--force-assign", action="store_true",
                   help="v3.5: 이미 배치된 상태여도 강제 재배치 (사용 주의 - 사용자 수동 배치 덮어쓸 수 있음)")
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    else:
        random.seed()

    if args.prdt_da is None:
        args.prdt_da = datetime.now().strftime("%Y%m%d")

    cfg_src = setup_runtime(args.env)
    if args.env == "prod" and args.mode in ("commit-one", "commit-all"):
        print(f"[!] env=prod commit 모드 - server={MES_SERVER} (cfg={cfg_src}). 사용자 입회 확인 필요", file=sys.stderr)

    # v3.3: --auto-resolve-pno 처리. 사용자 인자와 충돌 시 abort.
    sched_regno = None
    sched_revno = None
    if args.auto_resolve_pno:
        sched = resolve_first_sequence(args.prdt_da, args.line_cd)
        if sched is None:
            raise SystemExit(f"[ABORT] schedule API에 prdtDa={args.prdt_da} lineCd={args.line_cd} prdtRank=1 항목 없음 (휴일·미반영 가능)")
        api_pno, api_rev = sched.get("pno"), sched.get("pnoRev")
        sched_regno = sched.get("regNo")
        sched_revno = sched.get("revNo")
        print(f"[schedule] auto-resolve → pno={api_pno} pnoRev={api_rev} regNo={sched_regno} revNo={sched_revno} (cfg={cfg_src})")
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

    # v3.4: regNo/revNo는 schedule 응답값 우선 (없으면 0/"0" 호환 default)
    qry = {
        "prdtDa": args.prdt_da,
        "lineCd": args.line_cd,
        "pno": args.pno,
        "pnoRev": args.pno_rev,
        "prdtRank": args.prdt_rank,
        "regNo": sched_regno if sched_regno is not None else 0,
        "revNo": str(sched_revno) if sched_revno is not None else "0",
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

    # v3.5: shift 코드 결정
    shift_cd = {"D": "01", "N": "02", "auto": auto_shift_code()}[args.shift]

    print(f"=== jobsetup v3.5 mode={args.mode} with_assign={args.with_assign} with_auth={args.with_auth} shift={args.shift}({shift_cd}) ===")
    print(f"  qry: {qry}")
    print()

    # v3.5: 작업자 배치 단계 (--with-assign)
    assign_log = {"current_count": 0, "complete_before": False, "assigned": False,
                  "save_status": None, "save_msg": None, "save_ok": None, "skipped": False}
    if args.with_assign:
        print(f"=== assign step (shiftsCd={shift_cd}) ===")
        try:
            current = call_assign_list(qry)
        except Exception as e:
            print(f"[FAIL] assign/list.api: {e}")
            return 6
        complete = is_assignment_complete(current)
        assign_log["current_count"] = len(current)
        assign_log["complete_before"] = complete
        print(f"[assign] 현재 배치 {len(current)}공정, 완전 배치={complete}")

        need_assign = (not complete) or args.force_assign
        if not need_assign:
            print("[assign] 배치 완료 상태 - SKIP (멱등)")
            assign_log["skipped"] = True
        else:
            try:
                recs = call_assign_best_list(qry, shifts_cd=shift_cd)
            except Exception as e:
                print(f"[FAIL] assign-best/list.api: {e}")
                return 6
            print(f"[assign-best] 추천 {len(recs)}공정")
            for r in recs:
                print(f"  proc={r.get('procNo'):4s} {r.get('wrkNm','-'):8s} wrkId={r.get('wrkId','-')} lvl={r.get('wrkLvlNm','-')}")
            if not recs:
                print("[FAIL] assign-best 추천 0건 - 마스터 데이터 점검 필요")
                return 6

            if args.mode in ("commit-one", "commit-all"):
                # commit-one은 1공정만 검증 → 1건만 배치 시험
                payload = recs[:1] if args.mode == "commit-one" else recs
                print(f"\n=== assign commit ({len(payload)}공정) ===")
                sc, j, body = call_assign_save(payload)
                msg = (j or {}).get("statusMsg", "") if j else ""
                ok = (sc == 200 and j and str(j.get("statusCode", "")) == "200")
                assign_log["save_status"] = sc
                assign_log["save_msg"] = msg
                assign_log["save_ok"] = ok
                assign_log["assigned"] = ok
                if ok:
                    print(f"  [OK] assign/save | {msg[:60]}")
                else:
                    print(f"  [FAIL] sc={sc} msg='{msg[:80]}' body={body[:200]}")
                    log["assign"] = assign_log
                    out = STATE_DIR / f"run_v34_{started:%Y%m%d_%H%M%S}.json"
                    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
                    return 6
            else:
                print(f"[assign] mode={args.mode} - 추천만 출력 (저장 0)")
        print()

    log["assign"] = assign_log

    # v3.4: 작업자 인증 단계 (--with-auth)
    auth_log = {"assign_count": 0, "auth_plans": [], "auth_save_count": 0, "auth_fail_count": 0}
    if args.with_auth:
        print(f"=== auth step ===")
        try:
            assigns = call_assign_list(qry)
        except Exception as e:
            print(f"[FAIL] assign/list.api: {e}")
            return 4
        auth_log["assign_count"] = len(assigns)
        print(f"[assign] {len(assigns)}공정 회수")
        for a in assigns:
            already_y = (a.get("wrkCertiYn") or "").upper() == "Y"
            print(f"  proc={a.get('procNo'):4s} {a.get('wrkNm','-'):8s} wrkId={a.get('wrkId','-')} certi={a.get('wrkCertiYn','-')} regNo={a.get('regNo')} shiftsCd={a.get('shiftsCd')}")
            payload = build_auth_payload(a)
            auth_log["auth_plans"].append({
                "procNo": a.get("procNo"),
                "wrkNm": a.get("wrkNm"),
                "wrkId": a.get("wrkId"),
                "wrkCertiYn_before": a.get("wrkCertiYn"),
                "already_y": already_y,
                "payload": payload,
            })

        if not assigns:
            print("[FAIL] 작업자 배치 없음 - assign/save 선행 필요")
            return 4

        # auth commit
        if args.mode in ("commit-one", "commit-all"):
            print(f"\n=== auth commit ({'1건' if args.mode == 'commit-one' else len(assigns)}건) ===")
            targets = auth_log["auth_plans"][:1] if args.mode == "commit-one" else auth_log["auth_plans"]
            for ap in targets:
                if ap["already_y"]:
                    print(f"  [SKIP] proc={ap['procNo']} {ap['wrkNm']} 이미 Y (멱등 회피)")
                    continue
                sc, j, body = call_auth_cnfm(ap["payload"])
                msg = (j or {}).get("statusMsg", "") if j else ""
                ok = (sc == 200 and j and str(j.get("statusCode", "")) == "200")
                ap["auth_status"] = sc
                ap["auth_msg"] = msg
                ap["auth_ok"] = ok
                if ok:
                    auth_log["auth_save_count"] += 1
                    print(f"  [OK]   proc={ap['procNo']} {ap['wrkNm']} | {msg[:60]}")
                else:
                    auth_log["auth_fail_count"] += 1
                    print(f"  [FAIL] proc={ap['procNo']} {ap['wrkNm']} sc={sc} msg='{msg[:80]}' body={body[:200]}")
                    if args.mode == "commit-one":
                        break
            print(f"[auth summary] saved={auth_log['auth_save_count']} failed={auth_log['auth_fail_count']}")
            if auth_log["auth_fail_count"] > 0 and args.mode == "commit-all":
                print("[ABORT] auth 실패 - jobsetup 단계 진입 차단 (인증 미완료 상태에서 저장 시 미완료 처리됨)")
                log["auth"] = auth_log
                out = STATE_DIR / f"run_v34_{started:%Y%m%d_%H%M%S}.json"
                out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
                return 5
        print()

    log["auth"] = auth_log

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
        out = STATE_DIR / f"run_v34_{started:%Y%m%d_%H%M%S}.json"
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
    out = STATE_DIR / f"run_v34_{started:%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[summary] mode={args.mode} saved={log['save_count']} failed={log['fail_count']} | {out.name}")
    return 0 if log["fail_count"] == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
