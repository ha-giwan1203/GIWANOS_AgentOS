"""ERP D0추가생산지시 — A(야간) 행 삭제.
--test : 1건만 삭제 (SC0752 rank 10) + 전후 상태 비교
--all  : 모든 A 행 삭제 (단 주간 P/R/F와 EXT_PLAN_REG_NO 겹치는 건 기본 skip, --force-overlap 지정 시 포함)
"""
import sys, io, json, time, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

MAIN_MARK = "viewListDoAddnPrdtPlanInstrMngNew"
DEL_URL = "/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do"


def snapshot(page):
    return page.evaluate("""() => {
        const s = sGridList.$local_grid.pdata || [];
        const byStatus = {};
        s.forEach(r => { byStatus[r.WORK_STATUS_CD] = (byStatus[r.WORK_STATUS_CD]||0)+1; });
        return {
            total: s.length,
            byStatus,
            rows: s.map(r => ({status:r.WORK_STATUS_CD, rank:r.PRDT_RANK, prod:r.PROD_NO, ext:r.EXT_PLAN_REG_NO}))
        };
    }""")


def delete_one(page, row):
    """row = {EXT_PLAN_REG_NO, STD_DA, PLAN_DA, PROD_NO, LINE_CD}"""
    res = page.evaluate("""
    async (row) => {
        const param = JSON.stringify({
            EXT_PLAN_REG_NO: row.EXT_PLAN_REG_NO,
            STD_DA: row.STD_DA, PLAN_DA: row.PLAN_DA,
            PROD_NO: row.PROD_NO, LINE_CD: row.LINE_CD
        });
        return await new Promise((resolve) => {
            const to = setTimeout(() => resolve({ok:false, err:'timeout 15s'}), 15000);
            jQuery.ajax({
                url: '/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do',
                type: 'delete', data: param, contentType: 'application/json',
                success: r => { clearTimeout(to); resolve({ok:true, r}); },
                error: (xhr,s,e) => { clearTimeout(to); resolve({ok:false, httpStatus:xhr.status, err:String(e), body:(xhr.responseText||'').slice(0,400)}); }
            });
        });
    }
    """, row)
    return res


def refresh_sgrid(page):
    """현재 totSelectRowData / mSelectRowData 기준 s_grid 재조회."""
    page.evaluate("""() => {
        if (typeof mSelectRowData !== 'undefined' && mSelectRowData) {
            sGridList.searchListData({
                LINE_CD: mSelectRowData.LINE_CD,
                STD_DA: mSelectRowData.STD_DA,
                PLAN_DA: mSelectRowData.PLAN_DA,
                LINE_DIV_CD: mSelectRowData.LINE_DIV_CD,
                DAY_OPT: jQuery('#dayOpt').val()
            });
        }
    }""")
    time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_true", help="시험: 1건만 삭제 + 전후 비교")
    g.add_argument("--all", action="store_true", help="전체 A 행 삭제")
    ap.add_argument("--force-overlap", action="store_true", help="주간과 EXT 겹치는 것도 삭제")
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9223")
        page = None
        for pg in browser.contexts[0].pages:
            if MAIN_MARK in pg.url:
                page = pg; break
        if page is None:
            print("[ERROR] D0 탭 없음"); sys.exit(1)

        before = snapshot(page)
        print("[BEFORE]", json.dumps({"total":before["total"], "byStatus":before["byStatus"]}, ensure_ascii=False))

        # A 행 + 주간 EXT 집합
        a_rows = [r for r in before["rows"] if r["status"] == "A"]
        non_a_ext = {str(r["ext"]) for r in before["rows"] if r["status"] != "A"}

        # 테스트 모드: SC0752 한 건만
        if args.test:
            target = next((r for r in a_rows if r["prod"] == "RSP3SC0752"), None)
            if not target:
                print("[ERROR] SC0752 A행 없음"); sys.exit(2)
            # 삭제 payload 구성 — mSelectRowData 기반 STD_DA/PLAN_DA/LINE_CD
            meta = page.evaluate("() => ({STD_DA: mSelectRowData.STD_DA, PLAN_DA: mSelectRowData.PLAN_DA, LINE_CD: mSelectRowData.LINE_CD})")
            row = {"EXT_PLAN_REG_NO": target["ext"], "PROD_NO": target["prod"], **meta}
            print("[DELETE]", json.dumps(row, ensure_ascii=False))
            res = delete_one(page, row)
            print("[RESP]", json.dumps(res, ensure_ascii=False))
            refresh_sgrid(page)
            after = snapshot(page)
            print("[AFTER]", json.dumps({"total":after["total"], "byStatus":after["byStatus"]}, ensure_ascii=False))
            # diff
            before_ranks = {(r["status"], r["ext"]) for r in before["rows"]}
            after_ranks = {(r["status"], r["ext"]) for r in after["rows"]}
            removed = before_ranks - after_ranks
            added = after_ranks - before_ranks
            print(f"[DIFF] removed={removed} added={added}")
            return

        # --all 모드
        meta = page.evaluate("() => ({STD_DA: mSelectRowData.STD_DA, PLAN_DA: mSelectRowData.PLAN_DA, LINE_CD: mSelectRowData.LINE_CD})")
        to_delete = []
        for r in a_rows:
            if str(r["ext"]) in non_a_ext and not args.force_overlap:
                print(f"[SKIP overlap] {r['prod']} ext={r['ext']}")
                continue
            to_delete.append(r)
        print(f"[INFO] 삭제 대상 {len(to_delete)}건")

        done, fail = 0, 0
        for r in to_delete:
            row = {"EXT_PLAN_REG_NO": r["ext"], "PROD_NO": r["prod"], **meta}
            res = delete_one(page, row)
            ok = res.get("ok") and (res.get("r") or {}).get("statusCode") == "200"
            print(f"  del {r['prod']} ext={r['ext']} -> {'OK' if ok else 'FAIL'}")
            if ok: done += 1
            else: fail += 1; print(f"    {json.dumps(res, ensure_ascii=False)[:300]}")
            time.sleep(0.4)
        refresh_sgrid(page)
        after = snapshot(page)
        print(f"\n[AFTER] total={after['total']} byStatus={after['byStatus']}")
        print(f"[SUMMARY] deleted={done} failed={fail}")


if __name__ == "__main__":
    main()
