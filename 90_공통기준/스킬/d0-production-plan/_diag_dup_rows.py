"""5건 PROD_NO ERP D0 상단 그리드 행 개수 진단.

가설 (A): 같은 PROD_NO+PROD_DA 야간/주간 2행 공존 → idx_map 정렬만 고치면 해결
가설 (B): 1행만 = ERP 서버 새 ext 발행 거부 → 코드 수정만으로 안 됨

목적: phase3 multiList가 5건 신규 INSERT 했는지 실측 검증.
"""
from playwright.sync_api import sync_playwright
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import ensure_chrome_cdp, navigate_to_d0, CDP_URL

PROD_NOS = ["RSP3PC0130", "RSP3PC0129", "RSP3SC0644", "RSP3SC0590", "RSP3SC0584"]

ensure_chrome_cdp()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    page = navigate_to_d0(browser)

    # 상단 그리드 갱신
    page.evaluate("() => { try { totGridList.searchListData(); } catch(e){} }")
    page.wait_for_timeout(3000)

    # 5건 PROD_NO 행 dump
    result = page.evaluate("""(pnos) => {
        const d = jQuery('#grid_body').pqGrid('option','dataModel').data;
        const out = {};
        pnos.forEach(pno => {
            const rows = d.filter(r => r.PROD_NO === pno);
            out[pno] = rows.map(r => ({
                REG_NO: r.REG_NO,
                REG_DT: r.REG_DT,
                PROD_NO: r.PROD_NO,
                PRDT_QTY: r.PRDT_QTY,
                WORK_STATUS_CD: r.WORK_STATUS_CD,
                LINE_CD: r.LINE_CD,
                EXT_PLAN_YN: r.EXT_PLAN_YN
            }));
        });
        return out;
    }""", PROD_NOS)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    for pno in PROD_NOS:
        rows = result.get(pno, [])
        print(f"{pno}: {len(rows)}행", "→", [r["REG_NO"] for r in rows] if rows else "없음")
