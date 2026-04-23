"""
SmartMES 생산 스케줄 재정렬 자동화
- Excel 파일의 품번 순서대로 SmartMES [S] 스케줄 화면의 대기(R) 항목을 재배치
- 저장 버튼 좌표: (1265, 108) — 보조 모니터 기준
- 성공 메시지: "생산 서열을 변경 하였습니다."

사전 조건:
1. SmartMES 앱이 보조 모니터("LG FULL HD (2)")에 실행 중
2. [S] 스케줄 → 생산 스케줄 조정 화면 열려 있음
3. 해당 라인(SP3M3)과 오늘 날짜가 선택됨

실행:
  python smartmes_reorder.py                        # dry-run (계획만 표시)
  python smartmes_reorder.py --execute              # 실제 클릭 실행
  python smartmes_reorder.py --excel <path>         # Excel 경로 지정
  python smartmes_reorder.py --calibrate            # 좌표 캘리브레이션 모드
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import openpyxl
import pyautogui

# ============================================================
# 설정 (환경에 맞게 조정)
# ============================================================
CONFIG_FILE = Path(__file__).parent / "smartmes_reorder_config.json"

DEFAULTS = {
    # 저장 버튼 — 세션에서 검증된 좌표
    "save_button": {"x": 1265, "y": 108},

    # 스케줄 리스트 첫 행 중앙 Y 좌표 (1번 행)
    "first_row_y": None,

    # 행 간격 (픽셀, 행 중앙 간 거리)
    "row_pitch_y": None,

    # 품번 컬럼 중앙 X 좌표 (클릭으로 행 선택할 때)
    "pno_col_x": None,

    # ↑ 버튼 좌표 (선택된 행을 위로 올림)
    "up_button": {"x": None, "y": None},

    # ↓ 버튼 좌표 (선택된 행을 아래로 내림)
    "down_button": {"x": None, "y": None},

    # 성공 메시지 확인 대기 시간 (초)
    "save_wait_sec": 2.0,

    # 한 번 클릭 후 대기 시간
    "click_delay": 0.25,
}

EXCEL_DEFAULT = r"C:\Users\User\Desktop\SSKR D+0 추가생산 Upload.xlsx"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Merge defaults for missing keys
        for k, v in DEFAULTS.items():
            cfg.setdefault(k, v)
        return cfg
    return DEFAULTS.copy()


def save_config(cfg: dict) -> None:
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"[config] 저장: {CONFIG_FILE}")


# ============================================================
# Excel 읽기
# ============================================================
def read_excel_order(excel_path: str) -> list[str]:
    """
    Excel에서 품번 순서 읽기.
    헤더: 생산일 | 품번 | 생산량
    반환: 품번 리스트 (순서대로, 빈 행 제외)
    """
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    pnos = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[1] is None:
            continue
        pno = str(row[1]).strip()
        if pno:
            pnos.append(pno)
    return pnos


# ============================================================
# 현재 스케줄 읽기 (API — 빠르고 정확)
# ============================================================
def fetch_current_schedule() -> list[dict]:
    """
    SmartMES API로 현재 SP3M3 스케줄 조회.
    반환: items (prdtRank 순)
    """
    import urllib.request

    TOKEN = "bfee3f3d-caf9-434d-abbb-2cb015ec2469"
    BASE = "http://lmes-dev.samsong.com:19220"
    TODAY = datetime.now().strftime("%Y%m%d")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "tid": TOKEN, "token": TOKEN,
        "chnl": "MES", "from": "MESClient", "to": "MES",
        "usrid": "lmes",
        "Content-Type": "application/json",
    }
    body = json.dumps({"lineCd": "SP3M3", "prdtDa": TODAY}).encode()
    req = urllib.request.Request(f"{BASE}/v2/prdt/schdl/list.api",
                                 data=body, headers=headers)
    resp = urllib.request.urlopen(req, timeout=5)
    return json.loads(resp.read())["rslt"]["items"]


# ============================================================
# 재정렬 계획 산출
# ============================================================
def compute_plan(excel_pnos: list[str], current_items: list[dict]) -> list[tuple[int, int, str]]:
    """
    Excel 순서에 따라 shift:02 + workStatusCd:R 항목을 재정렬하는 계획.
    반환: [(from_rank, to_rank, pno), ...]  — 순서대로 적용해야 함
    """
    # 재정렬 대상: 대기(R) 상태만 (shift 무관 — 주간 작업분은 자동 제외됨)
    candidates = [x for x in current_items if x["workStatusCd"] == "R"]
    pno_to_rank = {x["pno"]: x["prdtRank"] for x in candidates}

    # Excel 순서에서 실제 후보에 존재하는 품번만 추출
    desired_order = [p for p in excel_pnos if p in pno_to_rank]
    current_order = sorted(candidates, key=lambda x: x["prdtRank"])
    current_ranks = [x["prdtRank"] for x in current_order]

    if len(desired_order) != len(current_order):
        missing = set(x["pno"] for x in current_order) - set(desired_order)
        extra = set(desired_order) - set(x["pno"] for x in current_order)
        print(f"[WARN] 불일치 — 현재에만 있음: {missing}, Excel에만 있음: {extra}")

    # 현재 배열 (mutable) 을 Excel 순서로 변환하면서 swap 순서 기록
    work = [x["pno"] for x in current_order]
    plan = []

    for target_idx, pno in enumerate(desired_order):
        if target_idx >= len(work):
            break
        if work[target_idx] == pno:
            continue
        # work 배열에서 pno 위치 찾기
        try:
            src_idx = work.index(pno, target_idx)
        except ValueError:
            print(f"[SKIP] {pno} — work 배열에 없음")
            continue

        # src_idx에서 target_idx로 한 칸씩 위로 (↑ 버튼)
        for i in range(src_idx, target_idx, -1):
            from_rank = current_ranks[i]
            to_rank = current_ranks[i - 1]
            plan.append((from_rank, to_rank, work[i]))
            work[i], work[i - 1] = work[i - 1], work[i]

    return plan


# ============================================================
# UI 조작
# ============================================================
def click_row(cfg: dict, rank: int, all_items: list[dict]) -> None:
    """rank 위치의 행을 클릭하여 선택."""
    # rank는 1부터 시작. 화면상 위치 계산
    # 화면에 보이는 순서대로 rank가 증가한다고 가정
    # 첫 행의 rank를 알아야 함 (보통 1)
    first_rank = min(x["prdtRank"] for x in all_items)
    row_index = rank - first_rank  # 0-based
    y = cfg["first_row_y"] + row_index * cfg["row_pitch_y"]
    x = cfg["pno_col_x"]
    pyautogui.click(x, y)
    time.sleep(cfg["click_delay"])


def click_up_button(cfg: dict) -> None:
    pyautogui.click(cfg["up_button"]["x"], cfg["up_button"]["y"])
    time.sleep(cfg["click_delay"])


def click_save(cfg: dict) -> None:
    pyautogui.click(cfg["save_button"]["x"], cfg["save_button"]["y"])
    time.sleep(cfg["save_wait_sec"])


# ============================================================
# 캘리브레이션 모드
# ============================================================
def calibrate(cfg: dict) -> dict:
    """마우스 위치로 좌표 순차 측정."""
    print("=" * 50)
    print("캘리브레이션 — 각 안내 후 해당 위치에 마우스 올리고 Enter")
    print("=" * 50)

    steps = [
        ("first_row_y", "스케줄 리스트 1번 행 중앙", "y"),
        ("row_pitch_y", "스케줄 리스트 2번 행 중앙 (간격 계산용)", "y"),
        ("pno_col_x", "품번 컬럼 중앙", "x"),
        ("up_button", "↑ (위로) 버튼 중앙", "xy"),
        ("down_button", "↓ (아래로) 버튼 중앙", "xy"),
        ("save_button", "저장 버튼 중앙 (기본 1265,108)", "xy"),
    ]

    measured = {}
    for key, label, kind in steps:
        input(f"\n→ {label} 위치에 마우스 올리고 Enter: ")
        x, y = pyautogui.position()
        if kind == "x":
            measured[key] = x
            print(f"  x={x}")
        elif kind == "y":
            measured[key] = y
            print(f"  y={y}")
        else:
            measured[key] = {"x": x, "y": y}
            print(f"  x={x}, y={y}")

    # row_pitch_y 계산
    first_y = measured["first_row_y"]
    second_y = measured["row_pitch_y"]
    measured["row_pitch_y"] = second_y - first_y
    measured["first_row_y"] = first_y
    print(f"\n[계산] row_pitch_y = {measured['row_pitch_y']}")

    cfg.update(measured)
    save_config(cfg)
    return cfg


def check_calibrated(cfg: dict) -> bool:
    required = ["first_row_y", "row_pitch_y", "pno_col_x"]
    for k in required:
        if cfg.get(k) is None:
            print(f"[ERROR] {k} 미설정 — --calibrate 로 먼저 캘리브레이션")
            return False
    for k in ["up_button"]:
        v = cfg.get(k, {})
        if v.get("x") is None or v.get("y") is None:
            print(f"[ERROR] {k} 좌표 미설정 — --calibrate 로 먼저 캘리브레이션")
            return False
    return True


# ============================================================
# 메인
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", default=EXCEL_DEFAULT, help="Excel 파일 경로")
    parser.add_argument("--execute", action="store_true", help="실제 클릭 실행 (미지정 시 dry-run)")
    parser.add_argument("--calibrate", action="store_true", help="좌표 캘리브레이션")
    args = parser.parse_args()

    cfg = load_config()

    if args.calibrate:
        calibrate(cfg)
        return

    # Excel 순서 읽기
    print(f"[1/4] Excel 읽기: {args.excel}")
    excel_pnos = read_excel_order(args.excel)
    print(f"  → {len(excel_pnos)}개 품번")

    # 현재 스케줄 API 조회
    print(f"[2/4] SmartMES API 조회")
    current = fetch_current_schedule()
    print(f"  → 전체 {len(current)}개 (shift:02+R 대상만 재정렬)")

    # 계획 산출
    print(f"[3/4] 재정렬 계획 계산")
    plan = compute_plan(excel_pnos, current)
    if not plan:
        print("  → 이미 Excel 순서와 일치. 재정렬 불필요.")
        return
    print(f"  → {len(plan)}회 ↑ 클릭 필요")
    for from_r, to_r, pno in plan:
        print(f"    {pno}: rank {from_r} → {to_r}")

    if not args.execute:
        print("\n[dry-run] 실제 실행하려면 --execute 추가")
        return

    # 실행
    print(f"[4/4] UI 자동화 실행 (5초 후 시작, Ctrl+C로 중단 가능)")
    for i in range(5, 0, -1):
        print(f"  {i}...", end="\r")
        time.sleep(1)
    print("  시작!      ")

    pyautogui.FAILSAFE = True  # 마우스 좌상단 이동 시 중단

    if not check_calibrated(cfg):
        sys.exit(1)

    for from_r, to_r, pno in plan:
        print(f"  {pno}: rank {from_r} → {to_r}")
        click_row(cfg, from_r, current)
        click_up_button(cfg)

    print("\n[저장] 저장 버튼 클릭")
    click_save(cfg)
    print("완료. 화면에서 '생산 서열을 변경 하였습니다.' 메시지 확인하세요.")


if __name__ == "__main__":
    main()
