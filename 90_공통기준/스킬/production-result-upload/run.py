"""MES 생산실적 자동 업로드 스크립트
- 일요일 실행 차단 (KST 기준)
- 전일 데이터만 업로드 (당일 절대 금지)
- CDP 브라우저 iframe jQuery 경유
"""
import json
import os
import shutil
import subprocess
import sys
import time

import openpyxl
import requests

KST_OFFSET = 9  # hours

def now_kst():
    from datetime import datetime, timezone, timedelta
    return datetime.now(timezone(timedelta(hours=KST_OFFSET)))


def is_sunday(d):
    return d.weekday() == 6


def refresh_bi():
    SRC = r"Z:\★ 라인별 생산실적\대원테크_라인별 생산실적_BI.xlsx"
    DST = r"C:\Users\User\Desktop\업무리스트\05_생산실적\BI실적\대원테크_라인별 생산실적_BI.xlsx"

    if not os.path.exists(SRC):
        print("WARNING: Z드라이브 접근 불가 — 로컬 파일 사용")
        if not os.path.exists(DST):
            print("FAIL: 로컬 BI 파일도 없음")
            sys.exit(1)
    else:
        src_mtime = os.path.getmtime(SRC)
        dst_mtime = os.path.getmtime(DST) if os.path.exists(DST) else 0
        if src_mtime > dst_mtime:
            shutil.copy2(SRC, DST)
            print("BI 파일 갱신 완료")
        else:
            print("BI 파일 이미 최신")
    return DST


def extract_bi(bi_path, target_date_str):
    from datetime import datetime as dt
    wb = openpyxl.load_workbook(bi_path, data_only=True, read_only=True)
    ws = wb.active

    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        date_val = row[7]
        if date_val is None:
            continue
        date_str = str(date_val)[:10]
        if date_str != target_date_str:
            continue

        item = {}
        for i in range(22):
            val = row[i]
            if val is None:
                val = ""
            elif isinstance(val, dt):
                val = val.strftime("%Y-%m-%d")
            elif isinstance(val, float):
                val = str(int(val)) if val == int(val) else str(round(val, 6))
            else:
                val = str(val)
            item[f"COL{i+1}"] = val
        items.append(item)

    wb.close()
    return items


def validate_items(items):
    empty_qty = [r for r in items if r.get("COL15") in (None, "", "0", "None")]
    if empty_qty:
        print(f"FAIL: 생산량 없는 행 {len(empty_qty)}/{len(items)}건 — 데이터 미완성")
        return False

    missing_core = [
        r for r in items
        if not r.get("COL1") or not r.get("COL5") or not r.get("COL8") or not r.get("COL15")
    ]
    if missing_core:
        print(f"WARNING: 핵심값 누락 {len(missing_core)}건 제외")
        items[:] = [r for r in items if r not in missing_core]

    return True


def upload_via_cdp(items, target_date_str):
    """CDP 브라우저의 iframe jQuery로 MES API 호출"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"FAIL: CDP 브라우저 연결 실패 — {e}")
            return False

        page = browser.contexts[0].pages[0]

        # MES 접속 확인
        current_url = page.url
        if "auth-dev" in current_url:
            print("FAIL: MES 로그인 필요 (auth-dev 리다이렉트)")
            return False

        # MES 레이아웃으로 이동
        if "layout/layout.do" not in current_url:
            page.goto("http://mes-dev.samsong.com:19200/layout/layout.do")
            page.wait_for_load_state("networkidle")
            time.sleep(3)

        # iframe 동적 탐지 + 생산실적 페이지 로드
        iframe_name = page.evaluate("""() => {
            const iframes = document.querySelectorAll('iframe[name]');
            return iframes.length > 0 ? iframes[0].name : null;
        }""")

        if not iframe_name:
            print("FAIL: iframe 없음")
            return False

        page.evaluate(f"""document.querySelector('iframe[name="{iframe_name}"]').src = '/prdtstatus/viewPrdtRsltByLine.do'""")
        time.sleep(3)

        has_jq = page.evaluate(f"""() => {{
            const f = document.querySelector('iframe[name="{iframe_name}"]');
            return !!(f && f.contentWindow && f.contentWindow.$);
        }}""")

        if not has_jq:
            print("FAIL: iframe jQuery 로드 실패")
            return False

        # 중복 확인
        existing = page.evaluate(f"""async () => {{
            const params = new URLSearchParams({{
                S_FROM: '{target_date_str}', S_TO: '{target_date_str}',
                S_CMPY_NM: '대원테크', pq_curPage: '1', pq_rPP: '1000'
            }});
            const resp = await fetch('/prdtstatus/selectPrdtRsltByLine.do?' + params);
            const result = await resp.json();
            return result.data.list.length;
        }}""")

        if existing > 0:
            print(f"STOP: MES에 {target_date_str} 데이터 {existing}건 이미 존재 — 중복 업로드 방지")
            return False

        # 업로드 (iframe jQuery)
        payload_json = json.dumps({"excelList": items}, ensure_ascii=False)
        result = page.evaluate(f"""async () => {{
            const iframe = document.querySelector('iframe[name="{iframe_name}"]');
            const $ = iframe.contentWindow.$;
            return new Promise((resolve) => {{
                $.ajax({{
                    url: "/prdtstatus/SaveExcelData.do",
                    type: "post",
                    data: JSON.stringify({json.dumps({"excelList": items}, ensure_ascii=False)}),
                    contentType: "application/json; charset=utf-8",
                    success: function(res) {{ resolve(res); }},
                    error: function(xhr, status, err) {{ resolve({{statusCode: "500", statusTxt: status + ' ' + err}}); }}
                }});
            }});
        }}""")

        status = result.get("statusCode", "?")
        print(f"업로드 응답: {status} — {result.get('statusTxt', '')}")

        if str(status) != "200" and str(status) != "OK":
            print("FAIL: 업로드 실패")
            return False

        # 검증
        time.sleep(2)
        verify = page.evaluate(f"""async () => {{
            const params = new URLSearchParams({{
                S_FROM: '{target_date_str}', S_TO: '{target_date_str}',
                S_CMPY_NM: '대원테크', pq_curPage: '1', pq_rPP: '1000'
            }});
            const resp = await fetch('/prdtstatus/selectPrdtRsltByLine.do?' + params);
            const result = await resp.json();
            const rows = result.data.list;
            const totalQty = rows.reduce((s, r) => s + Number(r.RESULT_QUANTITY || 0), 0);
            return {{ count: rows.length, totalQty }};
        }}""")

        return verify

    return False


def main():
    today = now_kst().date()
    from datetime import timedelta
    yesterday = today - timedelta(days=1)

    print(f"[MES 생산실적 업로드] 오늘={today}({['월','화','수','목','금','토','일'][today.weekday()]}), 대상={yesterday}")

    # ── 일요일 차단 (KST 기준) ──
    if is_sunday(today):
        print("일요일 — 실행 중단")
        sys.exit(0)

    target = yesterday.isoformat()

    # BI 갱신 + 추출
    bi_path = refresh_bi()
    items = extract_bi(bi_path, target)
    print(f"BI 추출: {target} → {len(items)}건")

    if len(items) == 0:
        print(f"STOP: BI 파일에 {target} 데이터 없음")
        sys.exit(0)

    # 품질 검증
    if not validate_items(items):
        sys.exit(1)

    bi_total_qty = sum(int(r["COL15"]) for r in items if r["COL15"].isdigit())
    print(f"BI 생산량 합계: {bi_total_qty:,}")

    # CDP 업로드
    result = upload_via_cdp(items, target)

    if result is False:
        sys.exit(1)

    if isinstance(result, dict):
        mes_count = result.get("count", 0)
        mes_qty = result.get("totalQty", 0)
        print(f"MES 검증: {mes_count}건, 생산량 합계 {int(mes_qty):,}")

        if mes_count != len(items):
            print(f"FAIL: 건수 불일치 (BI {len(items)} vs MES {mes_count})")
            sys.exit(1)
        if int(mes_qty) != bi_total_qty:
            print(f"FAIL: 생산량 합계 불일치 (BI {bi_total_qty:,} vs MES {int(mes_qty):,})")
            sys.exit(1)

        print("검증 PASS")
    else:
        print("업로드 완료 (검증 결과 없음)")

    print("완료")


if __name__ == "__main__":
    main()
