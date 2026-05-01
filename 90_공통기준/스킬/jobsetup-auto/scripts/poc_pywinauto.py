"""SmartMES 잡셋업 pywinauto PoC

좌표 의존성 0% 검증용. 실측 inspect 결과(2026-05-01) 기반:
- 제품 dropdown:    cbSchedule
- 공정 dropdown:    cbProcess
- 검사항목 dropdown: cbJobSetup
- X1/X2/X3 입력:    txtX1, txtX2, txtX3
- X1/X2/X3 OK 체크: chkOkX1, chkOkX2, chkOkX3
- 저장 버튼:        btnSave
- 메뉴 [J] 잡셋업:  btnMenuJobSetup

PoC 모드:
    --probe       : 식별만 (클릭 0건). 컨트롤 발견 여부 + handle 반환
    --select-only : 메뉴 진입 + 제품 1번 + 공정 1번 + 검사항목 1번 선택 (입력 0건, 저장 0건)
    --enter-only  : --select-only + X1/X2/X3 값 입력 (저장 0건)
    --commit      : 전체 + 저장 (절대 신중)

기본값 = --probe
"""
import argparse
import random
import sys
import time
from pathlib import Path

try:
    from pywinauto import Application, Desktop
except ImportError:
    sys.stderr.write("pywinauto missing - pip install pywinauto\n")
    sys.exit(2)


def gen_normal(center, lo, hi, decimals):
    half = min(center - lo, hi - center)
    sigma = half / 3.0
    while True:
        v = random.gauss(center, sigma)
        if lo <= v <= hi:
            return round(v, decimals)


def find_main_window():
    desktop = Desktop(backend="uia")
    for w in desktop.windows():
        try:
            t = w.window_text() or ""
            if "SAMSONG" in t.upper() or "SMART MES" in t.upper() or "SMART AGENT" in t.upper():
                return w.process_id(), t
        except Exception:
            pass
    return None, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["probe", "select-only", "enter-only", "commit"],
                   default="probe")
    args = p.parse_args()

    pid, title = find_main_window()
    if not pid:
        print("[FAIL] SmartMES main window not found")
        return 1
    print(f"[OK] mesclient.exe PID={pid} title='{title}'")

    app = Application(backend="uia").connect(process=pid)
    main_win = app.window(title_re=".*SAMSONG.*|.*SMART.*")

    # Step 1 — control discovery
    targets = {
        "menu_jobsetup":  ("btnMenuJobSetup",  "Button"),
        "menu_exit":      ("btnExit",          "Button"),
        "cb_product":     ("cbSchedule",       "ComboBox"),
        "cb_process":     ("cbProcess",        "ComboBox"),
        "cb_item":        ("cbJobSetup",       "ComboBox"),
        "txt_x1":         ("txtX1",            "Edit"),
        "txt_x2":         ("txtX2",            "Edit"),
        "txt_x3":         ("txtX3",            "Edit"),
        "chk_ok_x1":      ("chkOkX1",          "CheckBox"),
        "chk_ok_x2":      ("chkOkX2",          "CheckBox"),
        "chk_ok_x3":      ("chkOkX3",          "CheckBox"),
        "btn_save":       ("btnSave",          "Button"),
    }
    found = {}
    print("\n--- control probe ---")
    for key, (auto_id, ctrl_type) in targets.items():
        try:
            ctrl = main_win.child_window(auto_id=auto_id, control_type=ctrl_type)
            ctrl.wait("exists", timeout=3)
            r = ctrl.rectangle()
            print(f"  [OK]   {key:15s} auto_id={auto_id:20s} type={ctrl_type:9s} rect=({r.left},{r.top},{r.right},{r.bottom})")
            found[key] = ctrl
        except Exception as e:
            print(f"  [MISS] {key:15s} auto_id={auto_id:20s} type={ctrl_type:9s} err={e}")

    if args.mode == "probe":
        print(f"\n[probe done] {len(found)}/{len(targets)} controls identified")
        return 0 if len(found) == len(targets) else 2

    # Step 2 — selection
    if "menu_jobsetup" in found:
        print("\n[click] menu_jobsetup")
        found["menu_jobsetup"].click_input()
        time.sleep(1.0)

    # WinForms ComboBox는 표준 UIA SelectionPattern 미지원 → click + DOWN + ENTER 시퀀스
    def select_first(cb, label):
        try:
            cb.click_input()
            time.sleep(0.4)
            cb.type_keys("{DOWN}{ENTER}", set_foreground=False)
            print(f"[select] {label} (DOWN+ENTER)")
        except Exception as e:
            print(f"  {label} select failed: {e}")

    if "cb_product" in found:
        select_first(found["cb_product"], "cb_product (1.RSP3SC0646_A)")
        time.sleep(1.0)

    if "cb_process" in found:
        select_first(found["cb_process"], "cb_process (첫 공정)")
        time.sleep(2.0)

    if "cb_item" in found:
        select_first(found["cb_item"], "cb_item (첫 검사항목)")
        time.sleep(1.0)

    if args.mode == "select-only":
        print("\n[select-only done] no input, no save")
        return 0

    # Step 3 — input X1/X2/X3 (스펙 A1 0±0.05)
    spec = {"center": 0.0, "lo": -0.05, "hi": 0.05, "decimals": 2}
    v1 = gen_normal(**spec)
    v2 = gen_normal(**spec)
    v3 = gen_normal(**spec)
    print(f"\n[input] X1={v1} X2={v2} X3={v3}")

    for key, val in [("txt_x1", v1), ("txt_x2", v2), ("txt_x3", v3)]:
        if key in found:
            ctrl = found[key]
            try:
                ctrl.set_edit_text(f"{val:.2f}")
                print(f"  [OK] {key} <- {val:.2f}")
            except Exception as e:
                print(f"  [FAIL] {key}: {e}")

    # OK 체크
    for key in ("chk_ok_x1", "chk_ok_x2", "chk_ok_x3"):
        if key in found:
            try:
                if found[key].get_toggle_state() == 0:
                    found[key].toggle()
                print(f"  [OK] {key} checked")
            except Exception as e:
                print(f"  [WARN] {key} toggle: {e}")

    if args.mode == "enter-only":
        print("\n[enter-only done] no save")
        return 0

    # Step 4 — save
    if "btn_save" in found:
        print("\n[CAUTION] clicking save button...")
        time.sleep(1)
        found["btn_save"].click_input()
        time.sleep(2)
        print("[saved]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
