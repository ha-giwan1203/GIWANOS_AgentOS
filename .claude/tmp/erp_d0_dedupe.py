"""ERP D0추가생산지시 중복 등록 자동 식별 + 삭제.

[발견] 2026-04-27 세션110 — 사용자도 모르던 숨겨진 삭제 API
  URL: /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do (HTTP DELETE)
  payload: {REG_NO: <번호>}

[중복 식별 기준] SmartMES rank 순서 (api: /v2/prdt/schdl/list.api)
  - 같은 PROD_NO 쌍 중 rank 작은 쪽(위) 보존 / rank 큰 쪽(아래) 삭제
  - SmartMES `sewmacLabelScanQty` 필드 = ERP REG_NO 매핑 (필드명 misleading)

[안전 모드]
  --dry-run  : 식별만, 실제 DELETE 호출 안 함 (기본)
  --execute  : 실제 7건 일괄 DELETE (사용자 명시 동의 필수)
  --line     : SP3M3 (기본) / SD9A01
  --date     : YYYYMMDD (기본 오늘)

[사용 예]
  python erp_d0_dedupe.py --line SP3M3 --date 20260427           # dry-run
  python erp_d0_dedupe.py --line SP3M3 --date 20260427 --execute  # 실 삭제
"""
import sys, json, argparse, urllib.request
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, r"C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan")

SMARTMES_BASE = "http://lmes-dev.samsong.com:19220"
SMARTMES_TOKEN = "bfee3f3d-caf9-434d-abbb-2cb015ec2469"


def query_smartmes(line_cd: str, prdt_da: str):
    """SmartMES rank 순 조회. items 반환 (정렬됨)."""
    headers = {
        "Authorization": f"Bearer {SMARTMES_TOKEN}",
        "tid": SMARTMES_TOKEN, "token": SMARTMES_TOKEN,
        "chnl": "MES", "from": "MESClient", "to": "MES",
        "usrid": "lmes", "Content-Type": "application/json",
    }
    body = json.dumps({"lineCd": line_cd, "prdtDa": prdt_da}).encode()
    req = urllib.request.Request(f"{SMARTMES_BASE}/v2/prdt/schdl/list.api", data=body, headers=headers)
    items = json.loads(urllib.request.urlopen(req, timeout=5).read())["rslt"]["items"]
    return sorted(items, key=lambda x: x.get("prdtRank", 999))


def identify_dups(items):
    """SmartMES 데이터에서 중복 식별. (보존, 삭제) 분류 반환."""
    by_pno = defaultdict(list)
    for it in items:
        by_pno[it["pno"]].append(it)
    keeps, deletes = [], []
    for pno, rs in by_pno.items():
        rs_sorted = sorted(rs, key=lambda x: x.get("prdtRank", 999))
        keeps.append(rs_sorted[0])
        deletes.extend(rs_sorted[1:])
    return keeps, deletes


def execute_delete_via_erp(reg_nos):
    """Chrome 9223 + ERP D0 진입 후 jQuery DELETE 일괄 호출."""
    from playwright.sync_api import sync_playwright
    import run

    run.ensure_chrome_cdp()
    results = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(run.CDP_URL)
        page = run.navigate_to_d0(browser)
        for reg in reg_nos:
            res = page.evaluate("""
            async (regNo) => {
                return await new Promise((resolve) => {
                    const to = setTimeout(() => resolve({ok:false, err:'timeout 10s'}), 10000);
                    jQuery.ajax({
                        url: '/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do',
                        type: 'delete',
                        data: JSON.stringify({REG_NO: regNo}),
                        contentType: 'application/json',
                        success: (r) => { clearTimeout(to); resolve({ok:true, statusCode: r.statusCode, statusTxt: r.statusTxt}); },
                        error: (xhr,s,e) => { clearTimeout(to); resolve({ok:false, httpStatus:xhr.status, body:(xhr.responseText||'').slice(0,300)}); }
                    });
                });
            }
            """, reg)
            results.append((reg, res))
            print(f"  REG_NO={reg}: {res}")
        # 화면 갱신
        try:
            page.evaluate("() => { try { totGridList.searchListData(); } catch(e) {} }")
        except Exception:
            pass
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--line", default="SP3M3", help="라인 코드 (기본 SP3M3)")
    ap.add_argument("--date", default=datetime.now().strftime("%Y%m%d"), help="prdtDa YYYYMMDD (기본 오늘)")
    ap.add_argument("--execute", action="store_true", help="실제 DELETE 호출 (없으면 dry-run)")
    args = ap.parse_args()

    print(f"=== SmartMES 조회: line={args.line} date={args.date} ===")
    items = query_smartmes(args.line, args.date)
    print(f"총 {len(items)}건")

    keeps, deletes = identify_dups(items)
    print(f"\n보존: {len(keeps)}건 / 삭제 후보: {len(deletes)}건")

    if not deletes:
        print("\n중복 없음 — 종료"); return

    print("\n[보존 — rank 작은 쪽 = 위쪽]")
    for it in sorted(keeps, key=lambda x: x.get("prdtRank", 999)):
        print(f"  rank={it.get('prdtRank'):>3} pno={it.get('pno'):<14} qty={it.get('planQty'):>6} REG={it.get('sewmacLabelScanQty')}")
    print("\n[삭제 후보 — rank 큰 쪽 = 아래쪽]")
    for it in sorted(deletes, key=lambda x: x.get("prdtRank", 999)):
        print(f"  rank={it.get('prdtRank'):>3} pno={it.get('pno'):<14} qty={it.get('planQty'):>6} REG={it.get('sewmacLabelScanQty')}")

    if not args.execute:
        print("\n[dry-run] 실 DELETE 호출 안 함. --execute 옵션으로 실행.")
        return

    print(f"\n=== --execute: {len(deletes)}건 DELETE 실행 ===")
    reg_nos = [it.get("sewmacLabelScanQty") for it in deletes]
    results = execute_delete_via_erp(reg_nos)
    success = [(r, x) for r, x in results if x.get("ok") and str(x.get("statusCode")) == "200"]
    print(f"\n성공: {len(success)}/{len(results)}")
    if len(success) < len(results):
        print("실패 항목:")
        for r, x in results:
            if not (x.get("ok") and str(x.get("statusCode")) == "200"):
                print(f"  REG={r}: {x}")


if __name__ == "__main__":
    main()
