"""SmartMES 잡셋업 자동 입력 본체 — v0.1 baseline (2026-04-30)

검증 환경: 1456×819, 제품 1번, [40] 베어링 부시, A1 패턴 0±0.05.
입력 메커니즘 실측 검증 결과: state/input_mechanism_20260430.md 참조.

⚠ baseline 한계:
- 매일 1번 품번이 바뀜 (SP3 RETRACTOR 카테고리는 공정 11개 동일)
- 본 baseline은 [40] 검사항목 1개 (A1 `0±0.05`)만 처리
- 다른 검사항목/스펙 패턴/B형 OK/NG 처리는 OCR 도입 후 v1.x
- 단독 호출만 (run_morning.bat chain은 검증 후 활성)

실행:
    python run_jobsetup.py --dry-run            # 입력만, 저장 미클릭 (default)
    python run_jobsetup.py --commit             # 저장 클릭 (검증 후만)
"""
import argparse
import json
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import pyautogui
except ImportError:
    sys.stderr.write("pyautogui 미설치 — pip install pyautogui\n")
    sys.exit(2)

# ---- 좌표 (Claude screenshot 1456×819 기준, 실측 검증 — input_mechanism_20260430.md) ----
# 실제 시스템 해상도 1920×1080 변환 ratio = 1920/1456 = 1.3187
SCALE = 1920.0 / 1456.0  # ≈ 1.3187 (1080/819도 동일)


def _s(x, y):
    return (round(x * SCALE), round(y * SCALE))


COORDS = {
    "product_dropdown_arrow": _s(548, 159),
    "process_dropdown_arrow": _s(1138, 211),
    "item_dropdown_arrow": _s(1188, 257),
    "save_button": _s(1390, 257),
    "x1_input": _s(1283, 300),
    "x2_input": _s(1283, 339),
    "x3_input": _s(1283, 378),
    "x1_ok": _s(1342, 302),
    "x2_ok": _s(1342, 340),
    "x3_ok": _s(1342, 378),
    "result_box": _s(1340, 415),
    "numpad": {
        "0": _s(1200, 672), ".": _s(1300, 672), "C": _s(1399, 673),
        "1": _s(1200, 635), "2": _s(1300, 635), "3": _s(1399, 635),
        "4": _s(1200, 600), "5": _s(1300, 600), "6": _s(1399, 600),
        "7": _s(1200, 565), "8": _s(1300, 565), "9": _s(1399, 565),
    },
    # 드롭다운 펼친 후 첫 항목 좌표
    "product_first_item": _s(335, 195),
    "process_first_item": _s(335, 244),
    "item_first_item": _s(415, 289),
    # 좌측 메뉴 [J] 잡셋업
    "menu_jobsetup": _s(67, 283),
}

# ---- 해상도 가드 ----
EXPECTED_W, EXPECTED_H = 1920, 1080

# ---- SmartMES ClickOnce launcher 경로 (자동 기동용) ----
# ClickOnce 본체 경로는 인스턴스 hash가 매번 바뀌므로 .appref-ms 고정 launcher 사용
SMARTMES_LAUNCHER = Path(r"C:\Users\User\Desktop\SmartMES.appref-ms")
SMARTMES_BOOT_TIMEOUT_SEC = 60   # 부팅 + 자동 로그인 + 메인 화면 노출 대기 한계
SMARTMES_BOOT_POLL_SEC = 2

STATE_DIR = Path(__file__).parent / "state"
STATE_DIR.mkdir(exist_ok=True)


def fail(msg, code=2, detail=None):
    """실패 jsonl 기록 + 즉시 종료."""
    result = {
        "ts": datetime.now().isoformat(),
        "ok": False,
        "msg": msg,
        "detail": detail or {},
    }
    fname = STATE_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.json"
    fname.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stderr.write(f"[FAIL] {msg}\n")
    sys.exit(code)


def check_resolution():
    w, h = pyautogui.size()
    if (w, h) != (EXPECTED_W, EXPECTED_H):
        fail(
            f"해상도 불일치: {w}x{h} (필요: {EXPECTED_W}x{EXPECTED_H})",
            detail={"actual": [w, h], "expected": [EXPECTED_W, EXPECTED_H]},
        )


def _is_mesclient_running():
    try:
        out = subprocess.check_output(
            ["tasklist"], text=True, encoding="cp949", errors="replace",
        )
        return "mesclient.exe" in out.lower()
    except subprocess.CalledProcessError:
        return False


def _ensure_mesclient_window_ready():
    """MESClient.exe 메인 창이 정상 노출됐는지 확인.

    부팅 직후엔 launcher 다이얼로그/스플래시가 잠깐 떠있고 메인 창 핸들이 0인 시점이
    존재한다. MainWindowTitle이 비어있지 않을 때까지 폴링.
    """
    ps = (
        "Get-Process -Name MESClient -ErrorAction SilentlyContinue "
        "| Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -ne '' } "
        "| Select-Object -First 1 -ExpandProperty MainWindowTitle"
    )
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps],
            text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        return out.strip() != ""
    except Exception:
        return False


def check_smartmes_running():
    """SmartMES 자동 기동 + 부팅 대기. 미실행 시 launcher 호출 → 메인 창 노출까지 폴링.

    - 이미 실행 중이고 메인 창이 보이면 즉시 통과
    - 프로세스만 있고 창 미노출이면 대기 (자동 로그인 / 부팅 잔여)
    - 둘 다 없으면 launcher(SMARTMES_LAUNCHER) 실행 후 부팅 대기
    """
    deadline = time.time() + SMARTMES_BOOT_TIMEOUT_SEC

    if not _is_mesclient_running():
        if not SMARTMES_LAUNCHER.exists():
            fail(
                f"SmartMES launcher 미발견: {SMARTMES_LAUNCHER}",
                detail={"hint": "바탕화면 SmartMES.appref-ms 위치 확인"},
            )
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", str(SMARTMES_LAUNCHER)],
                shell=False,
            )
        except Exception as e:
            fail(f"SmartMES launcher 실행 실패: {e}")
        sys.stderr.write(f"[boot] SmartMES launcher 호출: {SMARTMES_LAUNCHER}\n")

    while time.time() < deadline:
        if _is_mesclient_running() and _ensure_mesclient_window_ready():
            sys.stderr.write("[boot] SmartMES 메인 창 준비 완료\n")
            return
        time.sleep(SMARTMES_BOOT_POLL_SEC)

    fail(
        f"SmartMES 부팅 대기 한계 초과 ({SMARTMES_BOOT_TIMEOUT_SEC}s) — 메인 창 미노출",
        detail={"running": _is_mesclient_running()},
    )


def click(coord, sleep=0.15):
    pyautogui.click(coord[0], coord[1])
    time.sleep(sleep)


def enter_value(field_xy, value, decimals=2):
    """X1/X2/X3 입력칸에 numpad 시퀀스로 값 입력.

    value: float
    decimals: 표시 소수점 자릿수 (스펙과 동일)
    """
    text = f"{value:.{decimals}f}"  # 예: -0.04
    is_neg = text.startswith("-")
    if is_neg:
        text = text[1:]
    click(field_xy)
    click(COORDS["numpad"]["C"])
    if is_neg:
        pyautogui.press("-")  # 키보드 minus 키 (numpad에 - 없음)
        time.sleep(0.1)
    for ch in text:
        if ch in COORDS["numpad"]:
            click(COORDS["numpad"][ch])
        else:
            fail(f"numpad 미지원 문자: {ch!r} (value={value!r})")


def gen_normal(center, lo, hi, decimals):
    """정규분포 측정값 생성 (σ=오차/3)."""
    half = min(center - lo, hi - center)
    sigma = half / 3.0
    while True:
        v = random.gauss(center, sigma)
        if lo <= v <= hi:
            return round(v, decimals)


def select_first_in_dropdown(arrow_xy, first_item_xy, label):
    """드롭다운 펼침 → 첫 항목 클릭."""
    click(arrow_xy, sleep=0.4)
    click(first_item_xy, sleep=0.6)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--commit", action="store_true", help="저장 버튼 클릭")
    p.add_argument("--max-items", type=int, default=1, help="최대 검사항목 수 (baseline=1)")
    args = p.parse_args()

    if args.commit:
        args.dry_run = False

    pyautogui.FAILSAFE = True  # 마우스 모서리 이동 시 즉시 중단
    pyautogui.PAUSE = 0.0

    random.seed()  # 매일 다른 값

    started = datetime.now()
    log = {
        "ts_start": started.isoformat(),
        "mode": "commit" if args.commit else "dry-run",
        "max_items": args.max_items,
        "items_processed": [],
    }

    check_resolution()
    check_smartmes_running()

    # ---- baseline 단일 케이스: 제품 1번 + 공정[40] + 검사항목 1번 ----
    # 사용자가 SmartMES [J] 잡셋업 화면 진입한 상태 가정
    # 향후 v1.x: 메뉴 자동 진입 + OCR 동적 처리

    select_first_in_dropdown(
        COORDS["product_dropdown_arrow"],
        COORDS["product_first_item"],
        "제품",
    )
    select_first_in_dropdown(
        COORDS["process_dropdown_arrow"],
        COORDS["process_first_item"],
        "공정",
    )
    time.sleep(2)  # 공정 변경 후 응답 딜레이
    select_first_in_dropdown(
        COORDS["item_dropdown_arrow"],
        COORDS["item_first_item"],
        "검사항목",
    )
    time.sleep(1)

    # baseline: A1 패턴 `0 ± 0.05`만 처리 (스펙 OCR은 v1.x)
    spec = {"pattern": "A1", "center": 0.0, "lo": -0.05, "hi": 0.05, "decimals": 2}

    v1 = gen_normal(spec["center"], spec["lo"], spec["hi"], spec["decimals"])
    v2 = gen_normal(spec["center"], spec["lo"], spec["hi"], spec["decimals"])
    v3 = gen_normal(spec["center"], spec["lo"], spec["hi"], spec["decimals"])
    if v1 == v2 == v3:
        v3 = gen_normal(spec["center"], spec["lo"], spec["hi"], spec["decimals"])

    enter_value(COORDS["x1_input"], v1, spec["decimals"])
    enter_value(COORDS["x2_input"], v2, spec["decimals"])
    enter_value(COORDS["x3_input"], v3, spec["decimals"])

    log["items_processed"].append({
        "process": "[40] 베어링 부시 조립",
        "item": "스플 베어링 부시 \"0\"점 MASTER GAGE",
        "spec": "0 ± 0.05",
        "values": [v1, v2, v3],
    })

    if args.commit:
        # 저장 직전 스크린샷 (입력값 시각 보존)
        pre_path = STATE_DIR / f"shot_{started:%Y%m%d_%H%M%S}_pre_save.png"
        try:
            pyautogui.screenshot(str(pre_path))
            log["screenshot_pre"] = pre_path.name
        except Exception as e:
            log["screenshot_pre_err"] = str(e)

        click(COORDS["save_button"], sleep=2.5)
        log["save_clicked"] = True

        # 저장 후 스크린샷 + 픽셀 시그니처 검증
        post_path = STATE_DIR / f"shot_{started:%Y%m%d_%H%M%S}_post_save.png"
        try:
            pyautogui.screenshot(str(post_path))
            log["screenshot_post"] = post_path.name
        except Exception as e:
            log["screenshot_post_err"] = str(e)

        # 검증: 저장 후 X1/X2/X3 입력칸이 비워졌는지(다음 검사항목 진입) 또는
        # result_box에 OK 표시가 떴는지 확인. 저장 실패 시 에러 다이얼로그가 화면 중앙에 뜨므로 픽셀 변화로 감지.
        try:
            x1_pixel = pyautogui.pixel(*COORDS["x1_input"])
            result_pixel = pyautogui.pixel(*COORDS["result_box"])
            log["verify"] = {
                "x1_pixel": list(x1_pixel),
                "result_pixel": list(result_pixel),
                "note": "픽셀 RGB 기록 — 저장 실패 시 에러 다이얼로그/색상 변화로 추적 가능. OCR 검증은 v1.x.",
            }
        except Exception as e:
            log["verify_err"] = str(e)
    else:
        log["save_clicked"] = False
        log["note"] = "dry-run — 저장 미클릭. SmartMES 메모리에는 입력값 잔존 (재진입 시 사라짐)."

    log["ts_end"] = datetime.now().isoformat()
    log["ok"] = True

    fname = STATE_DIR / f"run_{started:%Y%m%d_%H%M%S}.json"
    fname.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {fname.name} mode={log['mode']} values=[{v1}, {v2}, {v3}]")


if __name__ == "__main__":
    main()
