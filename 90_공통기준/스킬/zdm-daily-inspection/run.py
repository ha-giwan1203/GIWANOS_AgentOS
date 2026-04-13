"""ZDM 일상점검 자동 입력 스크립트 (SP3M3)
- 일요일 실행 차단 (KST 기준)
- 당일 점검 + 누락분 자동 보정
"""
import requests
import sys
from datetime import datetime, date, timezone, timedelta

BASE = "http://ax.samsong.com:34010"
KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    return datetime.now(KST)


def is_sunday(d: date) -> bool:
    return d.weekday() == 6


def get_sp3m3_masters() -> list:
    resp = requests.get(f"{BASE}/api/daily-inspection", timeout=10)
    resp.raise_for_status()
    all_data = resp.json()["data"]
    return sorted(
        [d for d in all_data if d["line_code"] == "SP3M3"],
        key=lambda x: x["inspection_no"],
    )


def get_items(master_id: str) -> list:
    resp = requests.get(f"{BASE}/api/daily-inspection/{master_id}/items", timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def get_entered_days(master_id: str, year_month: str) -> set:
    resp = requests.get(
        f"{BASE}/api/daily-inspection/{master_id}/records",
        params={"year_month": year_month},
        timeout=10,
    )
    resp.raise_for_status()
    return {
        r["check_day"]
        for r in resp.json().get("data", [])
        if r.get("check_result") == "OK"
    }


def post_ok(master_id: str, item_id: str, year_month: str, day: int) -> bool:
    payload = {
        "item_id": item_id,
        "year_month": year_month,
        "check_day": day,
        "check_result": "OK",
        "issue_desc": "",
        "action_taken": "",
        "manager_name": "",
        "worker_name": "작업자",
    }
    resp = requests.post(
        f"{BASE}/api/daily-inspection/{master_id}/record",
        json=payload,
        timeout=10,
    )
    return resp.status_code == 200 and resp.json().get("success", False)


def enter_day(masters: list, year_month: str, day: int) -> dict:
    ok = 0
    fail = 0
    for master in masters:
        items = get_items(master["id"])
        for item in items:
            if post_ok(master["id"], item["id"], year_month, day):
                ok += 1
            else:
                fail += 1
    return {"day": day, "ok": ok, "fail": fail}


def verify_day(masters: list, year_month: str, day: int) -> int:
    count = 0
    for master in masters:
        entered = get_entered_days(master["id"], year_month)
        if day in entered:
            # 해당 점검표에 입력된 건수를 정확히 셈
            resp = requests.get(
                f"{BASE}/api/daily-inspection/{master['id']}/records",
                params={"year_month": year_month},
                timeout=10,
            )
            for r in resp.json().get("data", []):
                if r.get("check_day") == day and r.get("check_result") == "OK":
                    count += 1
    return count


def find_missing_days(masters: list, year_month: str, up_to_day: int) -> list:
    """1일~up_to_day 중 일요일 제외, 미입력일 반환"""
    year, month = map(int, year_month.split("-"))
    first_master = masters[0]
    entered = get_entered_days(first_master["id"], year_month)

    missing = []
    for d in range(1, up_to_day + 1):
        dt = date(year, month, d)
        if is_sunday(dt):
            continue
        if d not in entered:
            missing.append(d)
    return missing


def main():
    today = now_kst().date()
    print(f"[ZDM 일상점검] {today} ({['월','화','수','목','금','토','일'][today.weekday()]})")

    # ── 일요일 차단 (KST 기준) ──
    if is_sunday(today):
        print("일요일 — 실행 중단")
        sys.exit(0)

    year_month = today.strftime("%Y-%m")
    masters = get_sp3m3_masters()
    if len(masters) != 19:
        print(f"FAIL: SP3M3 점검표 {len(masters)}개 (19개 아님)")
        sys.exit(1)

    # ── 당일 입력 ──
    result = enter_day(masters, year_month, today.day)
    print(f"당일({today.day}일): OK {result['ok']}건, 실패 {result['fail']}건")

    verified = verify_day(masters, year_month, today.day)
    if verified != 75:
        print(f"FAIL: 검증 {verified}/75")
        sys.exit(1)
    print(f"검증 PASS: {verified}/75")

    # ── 누락분 보정 (어제까지) ──
    missing = find_missing_days(masters, year_month, today.day - 1)
    if missing:
        print(f"누락일 발견: {missing}")
        for d in missing:
            dt = date(today.year, today.month, d)
            if is_sunday(dt):  # 이중 방어
                continue
            r = enter_day(masters, year_month, d)
            v = verify_day(masters, year_month, d)
            status = "PASS" if v == 75 else "FAIL"
            print(f"  {d}일 보정: OK {r['ok']}, 실패 {r['fail']}, 검증 {v}/75 {status}")
    else:
        print("누락일 없음")

    print("완료")


if __name__ == "__main__":
    main()
