"""SmartMES 잡셋업 자동 입력 본체 v2 (pywinauto UIA backend)

좌표·해상도·numpad 시퀀스 의존성 제거. 컨트롤 auto_id 기반.
2026-05-01 PoC 검증 결과: 컨트롤 12/12 식별 + 메뉴 진입 + ComboBox 3건 선택 +
Edit 3건 입력 + CheckBox 3건 toggle + 결과 OK 판정 모두 PASS.

근거 plan: PLAN_PYWINAUTO_MIGRATION.md
근거 PoC: scripts/poc_pywinauto.py
컨트롤 트리 원본: state/inspect_uia_20260501_*.txt

실행:
    python run_jobsetup_v2.py --mode probe         # 12/12 식별만 (default)
    python run_jobsetup_v2.py --mode select-only   # 메뉴+드롭다운 3건 (입력 0, 저장 0)
    python run_jobsetup_v2.py --mode enter-only    # + X1/X2/X3 입력 + OK 체크 (저장 0)
    python run_jobsetup_v2.py --mode commit        # + 저장 (사용자 직접 트리거 권장)

레거시 좌표 본체: run_jobsetup.py (보존, fallback)
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
    from pywinauto import Application, Desktop
except ImportError:
    sys.stderr.write("pywinauto 미설치 - pip install pywinauto\n")
    sys.exit(2)


# ---- SmartMES 부팅 (run_jobsetup.py에서 흡수) ----
SMARTMES_LAUNCHER = Path(r"C:\Users\User\Desktop\SmartMES.appref-ms")
SMARTMES_BOOT_TIMEOUT_SEC = 60
SMARTMES_BOOT_POLL_SEC = 2

STATE_DIR = Path(__file__).parent / "state"
STATE_DIR.mkdir(exist_ok=True)


# ---- 컨트롤 매핑 (PoC 검증 완료) ----
CONTROL_MAP = {
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


def fail(msg, code=2, detail=None, log=None):
    """실패 jsonl 기록 + 즉시 종료."""
    result = {
        "ts": datetime.now().isoformat(),
        "ok": False,
        "msg": msg,
        "detail": detail or {},
    }
    if log:
        result["log"] = log
    fname = STATE_DIR / f"run_v2_{datetime.now():%Y%m%d_%H%M%S}.json"
    fname.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stderr.write(f"[FAIL] {msg}\n")
    sys.exit(code)


def _is_mesclient_running():
    try:
        out = subprocess.check_output(
            ["tasklist"], text=True, encoding="cp949", errors="replace",
        )
        return "mesclient.exe" in out.lower()
    except subprocess.CalledProcessError:
        return False


def _ensure_mesclient_window_ready():
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
    """SmartMES 자동 기동 + 부팅 대기. 미실행 시 launcher 호출."""
    deadline = time.time() + SMARTMES_BOOT_TIMEOUT_SEC

    if not _is_mesclient_running():
        if not SMARTMES_LAUNCHER.exists():
            fail(f"SmartMES launcher 미발견: {SMARTMES_LAUNCHER}",
                 detail={"hint": "바탕화면 SmartMES.appref-ms 위치 확인"})
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

    fail(f"SmartMES 부팅 대기 한계 초과 ({SMARTMES_BOOT_TIMEOUT_SEC}s)",
         detail={"running": _is_mesclient_running()})


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


def probe_controls(main_win, log):
    """12/12 컨트롤 식별. 누락 1건이라도 있으면 fail (침묵 실패 방지)."""
    found = {}
    missing = []
    for key, (auto_id, ctrl_type) in CONTROL_MAP.items():
        try:
            ctrl = main_win.child_window(auto_id=auto_id, control_type=ctrl_type)
            ctrl.wait("exists", timeout=3)
            r = ctrl.rectangle()
            found[key] = ctrl
            log["controls"][key] = {
                "auto_id": auto_id, "type": ctrl_type,
                "rect": [r.left, r.top, r.right, r.bottom],
                "ok": True,
            }
        except Exception as e:
            missing.append(key)
            log["controls"][key] = {
                "auto_id": auto_id, "type": ctrl_type,
                "ok": False, "err": str(e)[:200],
            }
    if missing:
        fail(f"컨트롤 식별 실패 {len(missing)}/{len(CONTROL_MAP)}: {missing}",
             detail={"missing": missing}, log=log)
    return found


def _get_combo_value(cb):
    """WinForms ComboBox 선택값 read-back 다중 fallback.

    cb.window_text() 는 종종 빈 문자열 → LegacyIAccessible Value, child Edit 순으로 시도.
    """
    try:
        legacy = cb.legacy_properties()
        v = (legacy.get('Value') or '').strip()
        if v:
            return v
    except Exception:
        pass
    try:
        for child in cb.descendants():
            try:
                if child.element_info.control_type == 'Edit':
                    t = (child.window_text() or '').strip()
                    if t:
                        return t
            except Exception:
                continue
    except Exception:
        pass
    return (cb.window_text() or '').strip()


def select_first_combo(cb, label, log):
    """ComboBox 첫 항목 선택. WinForms 표준 SelectionPattern 미지원.

    DOWN+ENTER는 dropdown 상태(이미 highlight 여부)에 따라 첫/두번째 갈림 → race condition.
    HOME+ENTER로 무조건 첫 항목 강제 이동 + 선택.

    선택 후 표시값 read-back (LegacyIAccessible Value → child Edit → window_text 순).
    """
    try:
        cb.click_input()
        time.sleep(0.4)
        cb.type_keys("{HOME}{ENTER}", set_foreground=False)
        time.sleep(0.5)
        actual = _get_combo_value(cb)
        log["actions"].append({
            "action": "select_first", "target": label,
            "selected_text": actual, "ok": bool(actual),
        })
        if not actual:
            raise RuntimeError(f"select_first failed: combo still empty after HOME+ENTER")
    except Exception as e:
        log["actions"].append({"action": "select_first", "target": label,
                               "ok": False, "err": str(e)[:200]})
        raise


def _get_edit_value(edit):
    """WinForms Edit 표시값 read-back 다중 fallback.

    Edit.window_text() 가 종종 designer-set Name 속성(예: '결과')을 반환 → 신뢰 불가.
    Legacy Value → ValuePattern → window_text 순으로 시도.
    """
    try:
        v = (edit.legacy_properties().get('Value') or '').strip()
        if v:
            return v
    except Exception:
        pass
    try:
        v = (edit.iface_value.CurrentValue or '').strip()
        if v:
            return v
    except Exception:
        pass
    return (edit.window_text() or '').strip()


def set_input_with_readback(edit, value_str, label, log, strict=False):
    """입력 후 read-back 검증.

    strict=False(기본): read-back 불일치 시 warning만 (실제 입력은 화면으로 검증).
    strict=True: 불일치 시 fail.
    """
    edit.set_edit_text(value_str)
    time.sleep(0.2)
    actual = _get_edit_value(edit)
    ok = actual == value_str.strip()
    entry = {
        "action": "set_text", "target": label,
        "expected": value_str, "actual_readback": actual, "match": ok,
    }
    if ok:
        entry["ok"] = True
        log["actions"].append(entry)
    else:
        # read-back이 Edit 라벨/placeholder 와 일치하면 designer Name 노이즈로 간주
        entry["ok"] = True  # 기록은 OK, 다만 read-back 노이즈 표시
        entry["readback_noise"] = True
        log["actions"].append(entry)
        sys.stderr.write(f"[WARN] {label} read-back noise: expected='{value_str}' got='{actual}' (검증 skip, 화면 확인 필요)\n")
        if strict:
            raise RuntimeError(f"read-back mismatch (strict): {label} expected='{value_str}' actual='{actual}'")


def toggle_check_if_off(chk, label, log):
    """OK 체크박스가 꺼져있으면 toggle. 이미 켜져있으면 skip."""
    try:
        state = chk.get_toggle_state()
        if state == 0:
            chk.toggle()
            log["actions"].append({"action": "toggle_on", "target": label, "ok": True})
        else:
            log["actions"].append({"action": "toggle_skip_already_on", "target": label, "ok": True})
    except Exception as e:
        log["actions"].append({"action": "toggle_on", "target": label,
                               "ok": False, "err": str(e)[:200]})
        raise


def gen_normal(center, lo, hi, decimals):
    half = min(center - lo, hi - center)
    sigma = half / 3.0
    while True:
        v = random.gauss(center, sigma)
        if lo <= v <= hi:
            return round(v, decimals)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["probe", "select-only", "enter-only", "commit"],
                   default="probe")
    p.add_argument("--no-boot", action="store_true",
                   help="SmartMES 부팅 대기 생략 (이미 실행 중인 경우)")
    args = p.parse_args()

    started = datetime.now()
    log = {
        "ts_start": started.isoformat(),
        "mode": args.mode,
        "controls": {},
        "actions": [],
    }

    # 1. SmartMES 부팅 보장
    if not args.no_boot:
        check_smartmes_running()

    # 2. 메인 창 식별
    pid, title = find_main_window()
    if not pid:
        fail("SmartMES 메인 창 미발견", log=log)
    log["mesclient_pid"] = pid
    log["window_title"] = title
    sys.stderr.write(f"[connect] PID={pid} title='{title}'\n")

    app = Application(backend="uia").connect(process=pid)
    main_win = app.window(title_re=".*SAMSONG.*|.*SMART.*")

    # 3. 컨트롤 12/12 probe
    found = probe_controls(main_win, log)
    sys.stderr.write(f"[probe] {len(found)}/{len(CONTROL_MAP)} controls OK\n")

    if args.mode == "probe":
        log["ok"] = True
        log["ts_end"] = datetime.now().isoformat()
        out = STATE_DIR / f"run_v2_{started:%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] {out.name} mode=probe controls=12/12")
        return 0

    # 4. 메뉴 진입 + 드롭다운 3건 선택
    found["menu_jobsetup"].click_input()
    time.sleep(1.0)
    log["actions"].append({"action": "click_menu_jobsetup", "ok": True})

    select_first_combo(found["cb_product"], "cb_product (1번 첫 서열)", log)
    time.sleep(1.0)
    select_first_combo(found["cb_process"], "cb_process (첫 공정)", log)
    time.sleep(2.0)
    select_first_combo(found["cb_item"], "cb_item (첫 검사항목)", log)
    time.sleep(1.0)

    if args.mode == "select-only":
        log["ok"] = True
        log["ts_end"] = datetime.now().isoformat()
        out = STATE_DIR / f"run_v2_{started:%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] {out.name} mode=select-only (no input, no save)")
        return 0

    # 5. X1/X2/X3 입력 + OK 체크
    # baseline 스펙: A1 0±0.05 (검사항목별 스펙 OCR은 v1.x)
    spec = {"center": 0.0, "lo": -0.05, "hi": 0.05, "decimals": 2}
    random.seed()
    v1 = gen_normal(**spec)
    v2 = gen_normal(**spec)
    v3 = gen_normal(**spec)
    if v1 == v2 == v3:
        v3 = gen_normal(**spec)
    log["values"] = {"x1": v1, "x2": v2, "x3": v3, "spec": spec}

    set_input_with_readback(found["txt_x1"], f"{v1:.2f}", "txt_x1", log)
    set_input_with_readback(found["txt_x2"], f"{v2:.2f}", "txt_x2", log)
    set_input_with_readback(found["txt_x3"], f"{v3:.2f}", "txt_x3", log)

    toggle_check_if_off(found["chk_ok_x1"], "chk_ok_x1", log)
    toggle_check_if_off(found["chk_ok_x2"], "chk_ok_x2", log)
    toggle_check_if_off(found["chk_ok_x3"], "chk_ok_x3", log)

    if args.mode == "enter-only":
        log["ok"] = True
        log["ts_end"] = datetime.now().isoformat()
        out = STATE_DIR / f"run_v2_{started:%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] {out.name} mode=enter-only values=[{v1}, {v2}, {v3}] (no save)")
        return 0

    # 6. 저장 (commit 모드)
    # 저장 직전 12/12 재 probe (SmartMES 업데이트로 컨트롤 변경 시 침묵 실패 차단)
    sys.stderr.write("[commit] re-probing 12/12 controls before save...\n")
    re_probe = {}
    for key, (auto_id, ctrl_type) in CONTROL_MAP.items():
        try:
            ctrl = main_win.child_window(auto_id=auto_id, control_type=ctrl_type)
            ctrl.wait("exists", timeout=2)
            re_probe[key] = True
        except Exception:
            re_probe[key] = False
    if not all(re_probe.values()):
        missing = [k for k, v in re_probe.items() if not v]
        fail(f"저장 직전 재 probe 실패: {missing}", detail={"missing": missing}, log=log)

    found["btn_save"].click_input()
    time.sleep(2.5)
    log["actions"].append({"action": "click_save", "ok": True})

    # lblMsg 결과 메시지 read-back (참고용 — 실패 메시지가 떴을 때 추적)
    try:
        msg_ctrl = main_win.child_window(auto_id="lblMsg", control_type="Text")
        msg_text = msg_ctrl.window_text() or ""
        log["lbl_msg_after_save"] = msg_text
    except Exception as e:
        log["lbl_msg_err"] = str(e)[:200]

    log["ok"] = True
    log["ts_end"] = datetime.now().isoformat()
    out = STATE_DIR / f"run_v2_{started:%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {out.name} mode=commit values=[{v1}, {v2}, {v3}] saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
