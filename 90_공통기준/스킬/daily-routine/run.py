"""매일 반복 업무 통합 실행 (일요일 자동 차단, KST 기준)
1. ZDM 일상점검 (API 직호출)
2. MES 생산실적 업로드 (CDP iframe jQuery)
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, date, timedelta, timezone

import openpyxl
import requests

# ─── 공통 ───────────────────────────────────────────
KST = timezone(timedelta(hours=9))
DOW_KR = ["월", "화", "수", "목", "금", "토", "일"]

def now_kst():
    return datetime.now(KST)

def is_sunday(d):
    return d.weekday() == 6

def workdays_in_month(year, month, up_to_day):
    """1일~up_to_day 중 일요일 제외 날짜 리스트"""
    return [
        date(year, month, d)
        for d in range(1, up_to_day + 1)
        if date(year, month, d).weekday() != 6
    ]

# ─── ZDM ────────────────────────────────────────────
ZDM_BASE = "http://ax.samsong.com:34010"

def zdm_get_sp3m3():
    resp = requests.get(f"{ZDM_BASE}/api/daily-inspection", timeout=10)
    resp.raise_for_status()
    return sorted(
        [d for d in resp.json()["data"] if d["line_code"] == "SP3M3"],
        key=lambda x: x["inspection_no"],
    )

def zdm_get_items(master_id):
    resp = requests.get(f"{ZDM_BASE}/api/daily-inspection/{master_id}/items", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]

def zdm_entered_days(master_id, ym):
    resp = requests.get(f"{ZDM_BASE}/api/daily-inspection/{master_id}/records", params={"year_month": ym}, timeout=10)
    resp.raise_for_status()
    return {r["check_day"] for r in resp.json().get("data", []) if r.get("check_result") == "OK"}

def zdm_enter_day(masters, ym, day):
    ok = fail = 0
    for m in masters:
        for item in zdm_get_items(m["id"]):
            payload = {"item_id": item["id"], "year_month": ym, "check_day": day,
                       "check_result": "OK", "issue_desc": "", "action_taken": "",
                       "manager_name": "", "worker_name": "작업자"}
            try:
                r = requests.post(f"{ZDM_BASE}/api/daily-inspection/{m['id']}/record", json=payload, timeout=10)
                if r.status_code == 200 and r.json().get("success"):
                    ok += 1
                else:
                    fail += 1
            except:
                fail += 1
    return ok, fail

def zdm_verify_day(masters, ym, day):
    count = 0
    for m in masters:
        resp = requests.get(f"{ZDM_BASE}/api/daily-inspection/{m['id']}/records", params={"year_month": ym}, timeout=10)
        count += sum(1 for r in resp.json().get("data", []) if r.get("check_day") == day and r.get("check_result") == "OK")
    return count

def run_zdm(today):
    print("\n[1/2] ZDM 일상점검")
    ym = today.strftime("%Y-%m")
    masters = zdm_get_sp3m3()
    if len(masters) != 19:
        print(f"  FAIL: SP3M3 {len(masters)}개 (19 아님)")
        return False

    # 당일 입력
    ok, fail = zdm_enter_day(masters, ym, today.day)
    v = zdm_verify_day(masters, ym, today.day)
    print(f"  {today.day}일: {ok}건 OK, {fail}건 실패, 검증 {v}/75 {'PASS' if v==75 else 'FAIL'}")

    # 누락분 보정 (어제까지)
    entered = zdm_entered_days(masters[0]["id"], ym)
    for d in range(1, today.day):
        dt = date(today.year, today.month, d)
        if is_sunday(dt) or d in entered:
            continue
        ok2, fail2 = zdm_enter_day(masters, ym, d)
        v2 = zdm_verify_day(masters, ym, d)
        print(f"  {d}일 보정: {ok2}건 OK, 검증 {v2}/75 {'PASS' if v2==75 else 'FAIL'}")

    return True

# ─── MES ────────────────────────────────────────────
BI_SRC = r"Z:\★ 라인별 생산실적\대원테크_라인별 생산실적_BI.xlsx"
BI_DST = r"C:\Users\User\Desktop\업무리스트\05_생산실적\BI실적\대원테크_라인별 생산실적_BI.xlsx"

def mes_refresh_bi():
    if os.path.exists(BI_SRC):
        if os.path.getmtime(BI_SRC) > (os.path.getmtime(BI_DST) if os.path.exists(BI_DST) else 0):
            shutil.copy2(BI_SRC, BI_DST)
    elif not os.path.exists(BI_DST):
        print("  FAIL: BI 파일 없음")
        return None
    return BI_DST

def mes_extract(bi_path, target_str):
    wb = openpyxl.load_workbook(bi_path, data_only=True, read_only=True)
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        dv = row[7]
        if dv is None: continue
        ds = str(dv)[:10]
        if ds != target_str: continue
        item = {}
        for i in range(22):
            val = row[i]
            if val is None: val = ""
            elif isinstance(val, datetime): val = val.strftime("%Y-%m-%d")
            elif isinstance(val, float): val = str(int(val)) if val == int(val) else str(round(val, 6))
            else: val = str(val)
            item[f"COL{i+1}"] = val
        items.append(item)
    wb.close()
    return items

def mes_validate(items):
    return not any(r.get("COL15") in (None, "", "0", "None") for r in items)

def mes_upload_and_verify(page, iframe_name, items, target_str):
    """업로드 + 검증. 성공 시 (건수, 합계) 반환, 실패 시 None"""
    payload = json.dumps({"excelList": items}, ensure_ascii=False)
    result = page.evaluate(f"""async () => {{
        const iframe = document.querySelector('iframe[name="{iframe_name}"]');
        const $ = iframe.contentWindow.$;
        return new Promise((resolve) => {{
            $.ajax({{
                url: "/prdtstatus/SaveExcelData.do",
                type: "post",
                data: {json.dumps(payload)},
                contentType: "application/json; charset=utf-8",
                success: function(res) {{ resolve(res); }},
                error: function(x,s,e) {{ resolve({{statusCode:"500",statusTxt:s+' '+e}}); }}
            }});
        }});
    }}""")
    if str(result.get("statusCode", "")) not in ("200", "OK"):
        return None

    time.sleep(2)
    verify = page.evaluate(f"""async () => {{
        const params = new URLSearchParams({{
            S_FROM:'{target_str}',S_TO:'{target_str}',S_CMPY_NM:'대원테크',pq_curPage:'1',pq_rPP:'1000'
        }});
        const resp = await fetch('/prdtstatus/selectPrdtRsltByLine.do?'+params);
        const r = await resp.json();
        const rows = r.data.list;
        return {{count:rows.length, qty:rows.reduce((s,r)=>s+Number(r.RESULT_QUANTITY||0),0)}};
    }}""")
    return verify

def cdp_ensure_connected():
    """CDP 브라우저 연결 + MES 로그인까지 보장. (page, pw) 반환. 실패 시 (None, None)."""
    from playwright.sync_api import sync_playwright
    import pyautogui

    pw = sync_playwright().start()

    # 1. 연결 시도, 없으면 실행
    try:
        browser = pw.chromium.connect_over_cdp("http://localhost:9222")
    except:
        print("  CDP 미실행 -자동 시작")
        subprocess.Popen([
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "--remote-debugging-port=9222",
            r"--user-data-dir=C:\Users\User\.flow-chrome-debug",
            "http://mes-dev.samsong.com:19200/layout/layout.do",
            "--no-first-run", "--no-default-browser-check"
        ])
        time.sleep(6)
        try:
            browser = pw.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"  FAIL: CDP 연결 실패 -{e}")
            pw.stop()
            return None, None

    page = browser.contexts[0].pages[0]

    # 2. 로그인 필요 시 자동 로그인
    if "auth-dev" in page.url:
        print("  MES 로그인 시도...")
        try:
            page.bring_to_front()
            time.sleep(0.5)
            info = page.evaluate("()=>({screenX:window.screenX,screenY:window.screenY,chromeH:window.outerHeight-window.innerHeight})")
            box = page.locator('input[name="userId"]').bounding_box()
            sx = int(info['screenX'] + box['x'] + box['width']/2)
            sy = int(info['screenY'] + info['chromeH'] + box['y'] + box['height']/2)
            pyautogui.click(sx, sy)
            time.sleep(1.5)
            pyautogui.press('down')
            time.sleep(0.5)
            pyautogui.press('return')
            time.sleep(1.5)
            page.locator('button[type=submit]').first.click()
            time.sleep(5)
            # OAuth 후 auth-dev에 머무는 것은 정상 - MES로 직접 이동
            for attempt in range(3):
                try:
                    page.goto("http://mes-dev.samsong.com:19200/layout/layout.do", timeout=15000)
                    break
                except:
                    time.sleep(2)
            time.sleep(3)
            page.wait_for_load_state("domcontentloaded")
            if "mes-dev" not in page.url and "layout" not in page.url:
                print("  FAIL: 자동 로그인 실패")
                pw.stop()
                return None, None
            print("  MES 로그인 OK")
        except Exception as e:
            print(f"  FAIL: 로그인 에러 -{e}")
            pw.stop()
            return None, None

    return page, pw


def cdp_close(page, pw):
    """CDP 브라우저 정상 종료"""
    try:
        cdp = page.context.new_cdp_session(page)
        cdp.send("Browser.close")
    except:
        pass
    try:
        pw.stop()
    except:
        pass


def run_mes(today):
    print("\n[2/2] MES 생산실적 업로드")

    # BI 갱신
    bi = mes_refresh_bi()
    if not bi:
        return False

    page, pw = cdp_ensure_connected()
    if not page:
        return False

    # MES 레이아웃 확인 + iframe 대기
    if "layout/layout.do" not in page.url:
        try:
            page.goto("http://mes-dev.samsong.com:19200/layout/layout.do", timeout=15000)
        except:
            pass
        time.sleep(5)

    # iframe이 뜰 때까지 최대 15초 대기
    iframe_name = None
    for _ in range(5):
        iframe_name = page.evaluate("()=>{const f=document.querySelectorAll('iframe[name]');return f.length?f[0].name:null;}")
        if iframe_name:
            break
        time.sleep(3)

    if not iframe_name:
        print("  FAIL: iframe 없음")
        cdp_close(page, pw)
        return False

    page.evaluate(f"document.querySelector('iframe[name=\"{iframe_name}\"]').src='/prdtstatus/viewPrdtRsltByLine.do'")
    time.sleep(3)

    has_jq = page.evaluate(f"()=>{{const f=document.querySelector('iframe[name=\"{iframe_name}\"]');return !!(f&&f.contentWindow&&f.contentWindow.$);}}")
    if not has_jq:
        print("  FAIL: jQuery 미로드")
        cdp_close(page, pw)
        return False

    # MES 기등록 날짜 조회 (이번 달)
    ym = today.strftime("%Y-%m")
    first_day = date(today.year, today.month, 1).isoformat()
    yesterday = (today - timedelta(days=1)).isoformat()

    existing_raw = page.evaluate(f"""async () => {{
        const params = new URLSearchParams({{
            S_FROM:'{first_day}',S_TO:'{yesterday}',S_CMPY_NM:'대원테크',pq_curPage:'1',pq_rPP:'1000'
        }});
        const resp = await fetch('/prdtstatus/selectPrdtRsltByLine.do?'+params);
        const r = await resp.json();
        const byDate = {{}};
        for (const row of r.data.list) byDate[row.TRX_DA] = (byDate[row.TRX_DA]||0)+1;
        return byDate;
    }}""")
    mes_dates = set(existing_raw.keys())

    # BI 데이터 있는 날짜 (이번 달, 어제까지, 일요일 제외)
    wb = openpyxl.load_workbook(bi, data_only=True, read_only=True)
    ws = wb.active
    bi_dates = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        dv = row[7]
        if dv is None: continue
        ds = str(dv)[:10]
        if ds >= first_day and ds <= yesterday:
            bi_dates[ds] = bi_dates.get(ds, 0) + 1
    wb.close()

    # 누락일 산출
    targets = []
    for ds in sorted(bi_dates.keys()):
        dt = date.fromisoformat(ds)
        if is_sunday(dt):
            continue
        if ds not in mes_dates:
            targets.append(ds)

    has_fail = False
    if not targets:
        print("  누락 없음")
    else:
        print(f"  누락: {targets}")
        for t in targets:
            items = mes_extract(bi, t)
            if not items:
                print(f"  {t}: BI 0건 SKIP")
                continue
            if not mes_validate(items):
                print(f"  {t}: FAIL 생산량 빈값")
                has_fail = True
                continue

            bi_qty = sum(int(r["COL15"]) for r in items if r["COL15"].isdigit())
            v = mes_upload_and_verify(page, iframe_name, items, t)
            if v is None:
                print(f"  {t}: FAIL 업로드 실패")
                has_fail = True
                continue

            cnt_ok = v["count"] == len(items)
            qty_ok = int(v["qty"]) == bi_qty
            status_c = "OK" if cnt_ok else "FAIL"
            status_q = "OK" if qty_ok else "FAIL"
            print(f"  {t}: {v['count']}/{len(items)}건({status_c}), qty {int(v['qty']):,}/{bi_qty:,}({status_q})")
            if not cnt_ok or not qty_ok:
                has_fail = True

    cdp_close(page, pw)
    return not has_fail

# ─── main ───────────────────────────────────────────
def main():
    today = now_kst().date()
    print(f"=== 매일 반복 업무 === {today} ({DOW_KR[today.weekday()]})")

    if is_sunday(today):
        print("일요일 -전체 스킵")
        sys.exit(0)

    zdm_ok = run_zdm(today)
    mes_ok = run_mes(today)

    if zdm_ok and mes_ok:
        print("\n=== 완료 (ALL PASS) ===")
    else:
        failed = []
        if not zdm_ok:
            failed.append("ZDM")
        if not mes_ok:
            failed.append("MES")
        print(f"\n=== 완료 (FAIL: {', '.join(failed)}) ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
