"""SmartMES /v2/checksheet/check-result/jobsetup REST API PoC

근거 (디컴파일 직접 확인 — dnSpy GUI):
- ServiceAgent.SaveJobSetup(token, JobSetupItem):
    new RestRequest("v2/checksheet/check-result/jobsetup/save.api", Method.POST, DataFormat.Json)
    AddHeader("tid", Guid.NewGuid().ToString("N"))
    AddHeader("chnl", CommonConst.CHNL)        # = "lmes"
    AddHeader("from", CommonConst.FROM)        # = "lmes"
    AddHeader("to", CommonConst.TO)            # = "LMES"
    AddHeader("lang", CommonConst.LANG)        # = "ko"
    AddHeader("usrid", CommonConst.USRID)      # = "LMES"
    AddHeader("token", token)                  # = config Token
    AddJsonBody(JsonConvert.SerializeObject(param))
- ServiceAgent ctor: _client = new RestClient(Settings.Default.ApiServerMes)
    = http://lmes-dev.samsong.com:19220
- CommonConst.HTTP_RESULT_OK = "200"

목적:
1. read-only list.api로 인증+spec 검증 (저장 0)
2. 사용자 명시 후 save.api 시도
"""
import json
import sys
import uuid

import requests


CONFIG = {
    "MES_SERVER": "http://lmes-dev.samsong.com:19220",
    "TOKEN": "6c02224ce114410c8e53f45d1939a5b3",
}

COMMON_HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "chnl": "lmes",
    "from": "lmes",
    "to": "LMES",
    "lang": "ko",
    "usrid": "LMES",
    "token": CONFIG["TOKEN"],
}


def build_headers():
    """매 요청마다 새 tid 부여."""
    h = dict(COMMON_HEADERS)
    h["tid"] = uuid.uuid4().hex  # ToString("N") = 32-char no dashes
    return h


# JobSetupQRY (조회용 — ServiceAgent.GetJobSetup 시그니처)
# procNo 없이 호출 → 모든 공정 회수 시도
QRY_BASE = {
    "prdtDa": "20260502",
    "lineCd": "SP3M3",
    "pno": "RSP3SC0646",
    "pnoRev": "A",
    "prdtRank": 1,
    "regNo": 0,
    "revNo": "0",
    "procNo": "",
}


def call_list():
    """GET? POST? /v2/checksheet/check-result/jobsetup/list.api — 둘 다 시도."""
    url = f"{CONFIG['MES_SERVER']}/v2/checksheet/check-result/jobsetup/list.api"
    print(f"\n--- POST {url} ---")
    headers = build_headers()
    r = requests.post(url, json=QRY_BASE, headers=headers, timeout=15)
    print(f"  status={r.status_code} content-type={r.headers.get('content-type','-')}")
    print(f"  body[:500]={r.text[:500]!r}")
    if r.status_code == 200:
        try:
            j = r.json()
            sc = j.get("statusCode") or j.get("status") or "?"
            print(f"  json.statusCode={sc}")
            if str(sc) == "200":
                print(f"  [PASS] auth + path + headers OK")
                return j
        except Exception as e:
            print(f"  [json parse] {e}")
    return None


def main():
    print(f"=== SmartMES /v2 API PoC ===")
    print(f"  MES_SERVER: {CONFIG['MES_SERVER']}")
    print(f"  TOKEN:      {CONFIG['TOKEN'][:8]}...{CONFIG['TOKEN'][-4:]}")
    print(f"  QRY_BASE:   {QRY_BASE}")

    result = call_list()
    if result:
        items = result.get("rslt", {}).get("items", [])
        print(f"\n=== list.api items count: {len(items)} ===")
        # 공정별 그룹
        by_proc = {}
        for it in items:
            key = (it.get("procNo"), it.get("mngAriclCd"))
            by_proc.setdefault(it.get("procNo"), []).append(it)
        for proc_no in sorted(by_proc.keys() or []):
            its = by_proc[proc_no]
            print(f"\n  procNo={proc_no} count={len(its)}")
            for it in its:
                spec = it.get("mngAriclCmnt", "")
                std = it.get("stdDivCd", "")
                std_nm = it.get("stdDivNm", "")
                rslt = it.get("finalCheckRsltCd", "")
                x1 = it.get("x1", "")
                nm = it.get("mngAriclNm", "")[:35]
                print(f"    [{it.get('mngAriclCd')}] {nm:35s} std={std}({std_nm}) spec='{spec}' rslt={rslt} x1={x1!r}")
        # 첫 1개 raw 표시 (스키마 검증용)
        if items:
            print("\n=== sample item (full schema) ===")
            print(json.dumps(items[0], ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
