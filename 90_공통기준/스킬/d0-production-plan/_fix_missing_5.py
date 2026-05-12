"""evening 세션 누락 5건 야간 추가 등록.

조건:
- 기존 잘못 박힌 rank (ext=325225~325230 위 A rank) 삭제 안 함
- 5건 PROD_NO 야간 신규 ext (325983~325987)에 phase4 process_one_row 호출 + final_save
- sendMesFlag='Y' final_save로 MES 전송
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from run import (
    ensure_chrome_cdp, navigate_to_d0, CDP_URL,
    process_one_row, final_save, LINE_CONFIG,
)

# 5건 PROD_NO + 새 ext (진단 스크립트 실측 결과)
FIXES = [
    ("RSP3PC0130", 325983),
    ("RSP3PC0129", 325984),
    ("RSP3SC0644", 325985),
    ("RSP3SC0590", 325986),
    ("RSP3SC0584", 325987),
]
TARGET_LINE = "SP3M3"
SAVE_URL = LINE_CONFIG[TARGET_LINE]["save_url"]

ensure_chrome_cdp()

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    page = navigate_to_d0(browser)

    # 상단 그리드 갱신
    page.evaluate("() => { try { totGridList.searchListData(); } catch(e){} }")
    page.wait_for_timeout(3000)

    done, failed = [], []
    for pno, ext in FIXES:
        print(f"\n[fix] {pno} ext={ext}")
        r = process_one_row(page, pno, ext, TARGET_LINE, SAVE_URL, dry_run=False)
        if not r.get("ok"):
            print(f"  [fail] {r}")
            failed.append({"pno": pno, "ext": ext, "err": r})
            continue
        rr = (r.get("r") or {})
        if str(rr.get("statusCode")) != "200":
            print(f"  [fail] multiList statusCode != 200: {r}")
            failed.append({"pno": pno, "ext": ext, "err": r})
            continue
        print(f"  [ok] addedRank={r.get('addedRank')} dataListLen={r.get('dataListLen')}")
        done.append({"pno": pno, "ext": ext, "rank": r.get("addedRank")})

    print(f"\n=== 임시저장 결과: 성공 {len(done)}건 / 실패 {len(failed)}건 ===")
    if failed:
        print("실패 목록:", failed)
        print("final_save 보류")
        raise SystemExit(2)

    # final_save (sendMesFlag='Y') — MES 전송
    print("\n[phase5] final_save 진행")
    final_save(page, SAVE_URL)
    print("\n=== 누락 5건 추가 등록 + MES 전송 완료 ===")
