"""SmartMES 잡셋업 자동 입력 본체 v2.1 — 전 공정·전 검사항목 순회

근거 자료: state/screen_analysis_20260429.md (11공정 17항목 + 스펙 패턴 6종 분류)
근거 마이그레이션: PLAN_PYWINAUTO_MIGRATION.md (v2.0 = 좌표 의존성 제거)

v2.1 변경점:
- 11개 공정 자동 순회
- 각 공정의 모든 검사항목(N≥1) 자동 순회
- dgvJobSetup 첫 행 `스펙` 컬럼 텍스트 read-back
- 정규식 기반 A/B 분기 (A=측정값형 정규분포 난수 / B=OK/NG형 빈칸+OK 체크)
- 검사항목 단위 저장 (저장 단위는 첫 실행 관찰 후 조정 가능)

모드 5종:
    enum-only    : 공정·검사항목·spec 텍스트만 dump (저장 0, 입력 0)
    dry-run      : enum + 입력만 (저장 0)
    commit-one   : 첫 공정 첫 검사항목 1건만 commit (검증용)
    commit-process : 첫 공정 모든 검사항목 commit
    commit-all   : 모든 공정 모든 검사항목 commit (운영)

기본값: enum-only

❌ NG 자동 체크 금지 (NG는 사람 판정만, B형은 OK만 자동)
❌ 무인 자동 실행 금지 (사용자 입회 시에만)
"""
import argparse
import json
import random
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from pywinauto import Application, Desktop
except ImportError:
    sys.stderr.write("pywinauto missing - pip install pywinauto\n")
    sys.exit(2)

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.0
except ImportError:
    sys.stderr.write("pyautogui missing - pip install pyautogui\n")
    sys.exit(2)


SMARTMES_LAUNCHER = Path(r"C:\Users\User\Desktop\SmartMES.appref-ms")
SMARTMES_BOOT_TIMEOUT_SEC = 60
SMARTMES_BOOT_POLL_SEC = 2

STATE_DIR = Path(__file__).parent / "state"
STATE_DIR.mkdir(exist_ok=True)


CONTROL_MAP = {
    "menu_jobsetup":  ("btnMenuJobSetup",  "Button"),
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
    "grid":           ("dgvJobSetup",      "Table"),
    "lbl_msg":        ("lblMsg",           "Text"),
}


# ---- spec 분류 (screen_analysis_20260429.md 기준) ----

# A1: 대칭 단순 — `0 ± 0.05`
RE_A1 = re.compile(r"^\s*([-+]?\d+(?:\.\d+)?)\s*[±]\s*(\d+(?:\.\d+)?)\s*\w*\s*$")
# A2: 비대칭 + 단위 — `10.5 +0.1mm, -0.3mm`
RE_A2 = re.compile(
    r"([-+]?\d+(?:\.\d+)?)\s*\+(\d+(?:\.\d+)?)\s*\w*\s*,?\s*-(\d+(?:\.\d+)?)\s*\w*"
)


def classify_spec(text):
    """스펙 텍스트 → ('A', params) 또는 ('B', None) 반환.

    params for A: list of (lo, hi, decimals) — 복합 비대칭(A3)일 경우 다수
    """
    if not text:
        return ("B", None)
    s = text.strip()

    # A1 시도
    m = RE_A1.match(s)
    if m:
        center = float(m.group(1))
        tol = float(m.group(2))
        decimals = max(_dec_count(m.group(1)), _dec_count(m.group(2)))
        return ("A", [(center - tol, center + tol, decimals)])

    # A2 / A3 시도 (1회 이상)
    matches = list(RE_A2.finditer(s))
    if matches:
        ranges = []
        for m in matches:
            center = float(m.group(1))
            up = float(m.group(2))
            dn = float(m.group(3))
            decimals = max(_dec_count(m.group(1)),
                           _dec_count(m.group(2)),
                           _dec_count(m.group(3)))
            ranges.append((center - dn, center + up, decimals))
        # A3 = 다수 매칭 → 교집합
        if len(ranges) > 1:
            lo = max(r[0] for r in ranges)
            hi = min(r[1] for r in ranges)
            decimals = max(r[2] for r in ranges)
            return ("A", [(lo, hi, decimals)])
        return ("A", ranges)

    # 그 외 = B형 fallback
    return ("B", None)


def _dec_count(s):
    if "." in s:
        return len(s.split(".")[1])
    return 0


def gen_normal_in_range(lo, hi, decimals):
    """[lo, hi] 범위 내 정규분포 난수 (σ = 반폭/3)."""
    center = (lo + hi) / 2.0
    half = (hi - lo) / 2.0
    sigma = half / 3.0
    while True:
        v = random.gauss(center, sigma)
        if lo <= v <= hi:
            return round(v, decimals)


# ---- SmartMES 부팅 보장 ----

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


def fail(msg, code=2, detail=None, log=None):
    result = {
        "ts": datetime.now().isoformat(),
        "ok": False,
        "msg": msg,
        "detail": detail or {},
    }
    if log:
        result["log"] = log
    fname = STATE_DIR / f"run_v21_{datetime.now():%Y%m%d_%H%M%S}.json"
    fname.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stderr.write(f"[FAIL] {msg}\n")
    sys.exit(code)


def check_smartmes_running():
    deadline = time.time() + SMARTMES_BOOT_TIMEOUT_SEC
    if not _is_mesclient_running():
        if not SMARTMES_LAUNCHER.exists():
            fail(f"SmartMES launcher 미발견: {SMARTMES_LAUNCHER}")
        try:
            subprocess.Popen(["cmd", "/c", "start", "", str(SMARTMES_LAUNCHER)], shell=False)
        except Exception as e:
            fail(f"SmartMES launcher 실행 실패: {e}")
    while time.time() < deadline:
        if _is_mesclient_running() and _ensure_mesclient_window_ready():
            return
        time.sleep(SMARTMES_BOOT_POLL_SEC)
    fail(f"SmartMES 부팅 대기 한계 초과 ({SMARTMES_BOOT_TIMEOUT_SEC}s)")


def find_main_pid():
    desktop = Desktop(backend="uia")
    for w in desktop.windows():
        try:
            t = w.window_text() or ""
            if "SAMSONG" in t.upper() or "SMART" in t.upper():
                return w.process_id(), t
        except Exception:
            pass
    return None, None


# ---- ComboBox / Edit / Grid helper ----

def get_combo_value(cb):
    try:
        v = (cb.legacy_properties().get('Value') or '').strip()
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


def get_edit_value(edit):
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


def fresh_ctrl(get_main_win, key):
    """매 호출마다 main_win + control 새로 resolve (lazy resolve 실패 회피)."""
    auto_id, ctrl_type = CONTROL_MAP[key]
    mw = get_main_win()
    c = mw.child_window(auto_id=auto_id, control_type=ctrl_type)
    c.wait("exists", timeout=5)
    return c


def get_ctrl_center(get_main_win, key):
    """pywinauto rect → 화면 절대 좌표 center 반환 (multi-monitor 안전)."""
    cb = fresh_ctrl(get_main_win, key)
    r = cb.rectangle()
    return (r.left + r.right) // 2, (r.top + r.bottom) // 2


def select_by_index_fresh(get_main_win, key, idx, settle=0.6, retries=2):
    """ComboBox idx번째 항목 선택 — pywinauto rect + pyautogui click/keyboard.

    pywinauto의 click_input은 multi-monitor 환경에서 main_win lazy resolve race.
    rect만 pywinauto에서 받고 click/keyboard는 pyautogui로 처리 → 안정적.
    """
    last_val = ""
    last_err = None
    for attempt in range(retries + 1):
        try:
            cx, cy = get_ctrl_center(get_main_win, key)
            pyautogui.click(cx, cy)
            time.sleep(0.6)  # dropdown 펼침
            pyautogui.press("home")
            time.sleep(0.3)
            for _ in range(idx):
                pyautogui.press("down")
            if idx > 0:
                time.sleep(0.3)
            pyautogui.press("enter")
            time.sleep(settle)
            cb_read = fresh_ctrl(get_main_win, key)
            last_val = get_combo_value(cb_read)
            if last_val:
                return last_val
            time.sleep(0.5)
        except Exception as e:
            last_err = e
            if attempt < retries:
                try:
                    pyautogui.press("escape")
                except Exception:
                    pass
                time.sleep(1.5)
                continue
            raise
    return last_val


def get_grid_first_row_spec(grid):
    """dgvJobSetup 첫 행의 `스펙` 컬럼 텍스트 추출.

    inspect 결과: grid의 children = rows, 각 row의 descendants 중 Text/Edit 타입.
    스펙 컬럼은 보통 첫 셀 (헤더 보면 [스펙, x1, 결과, x2, 결과, x3, 결과, 문제점, 조치내용]).
    """
    try:
        rows = grid.children()
        if not rows:
            return ""
        first_row = rows[0]
        # 첫 셀 = 스펙. 헤더가 없으면 children[0]
        # WinForms DataGridView의 cells 는 row.children() 또는 descendants() 로 접근
        cells = []
        for d in first_row.descendants():
            try:
                ct = d.element_info.control_type
                if ct in ("Text", "Edit", "Custom", "DataItem"):
                    t = (d.window_text() or "").strip()
                    if t:
                        cells.append(t)
            except Exception:
                continue
        if cells:
            return cells[0]  # 첫 셀 = 스펙
    except Exception:
        pass
    return ""


def enum_combo_fresh(get_main_win, key, max_count, settle_per=0.5):
    """ComboBox 모든 항목 enum (fresh resolve, race-free)."""
    seen = []
    for idx in range(max_count):
        val = select_by_index_fresh(get_main_win, key, idx, settle=settle_per)
        if not val:
            break
        if seen and val == seen[-1]:
            break
        seen.append(val)
    return seen


# ---- 안전 입력/체크 ----

def set_input(edit, value_str, label, log):
    edit.set_edit_text(value_str)
    time.sleep(0.2)
    actual = get_edit_value(edit)
    log["actions"].append({
        "action": "set_text", "target": label,
        "expected": value_str, "actual": actual,
        "ok": True,
    })


def clear_input(edit, label, log):
    """B형 — 입력칸 비움."""
    edit.set_edit_text("")
    time.sleep(0.15)
    log["actions"].append({"action": "clear", "target": label, "ok": True})


def toggle_ok_if_off(chk, label, log):
    try:
        state = chk.get_toggle_state()
        if state == 0:
            chk.toggle()
            log["actions"].append({"action": "ok_on", "target": label, "ok": True})
        else:
            log["actions"].append({"action": "ok_skip", "target": label, "ok": True})
    except Exception as e:
        log["actions"].append({"action": "ok_on", "target": label,
                               "ok": False, "err": str(e)[:200]})
        raise


# ---- 메인 흐름 ----

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode",
                   choices=["enum-only", "dry-run", "commit-one", "commit-process", "commit-all"],
                   default="enum-only")
    p.add_argument("--no-boot", action="store_true")
    p.add_argument("--limit-process", type=int, default=15)
    p.add_argument("--limit-item", type=int, default=15)
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
    else:
        random.seed()

    started = datetime.now()
    log = {
        "ts_start": started.isoformat(),
        "mode": args.mode,
        "product": None,
        "processes": [],
        "save_count": 0,
        "fail_count": 0,
    }

    if not args.no_boot:
        check_smartmes_running()

    pid, title = find_main_pid()
    if not pid:
        fail("SmartMES 메인 창 미발견", log=log)
    log["mesclient_pid"] = pid
    log["window_title"] = title
    sys.stderr.write(f"[connect] PID={pid} title='{title}'\n")

    app = Application(backend="uia").connect(process=pid)

    def get_main_win():
        return app.window(title_re=".*SAMSONG.*|.*SMART.*")

    # 메뉴 진입 보장
    main_win = get_main_win()
    menu = main_win.child_window(auto_id="btnMenuJobSetup", control_type="Button")
    menu.wait("exists", timeout=3)
    menu.click_input()
    time.sleep(3.0)

    # 컨트롤 12개 식별 검증 (실제 사용은 매번 fresh resolve)
    for key, (auto_id, ctrl_type) in CONTROL_MAP.items():
        try:
            c = get_main_win().child_window(auto_id=auto_id, control_type=ctrl_type)
            c.wait("exists", timeout=3)
        except Exception as e:
            fail(f"컨트롤 미발견: {key} ({auto_id})", detail={"err": str(e)[:200]}, log=log)

    # 제품 첫 서열 선택
    product = select_by_index_fresh(get_main_win, "cb_product", 0, settle=1.5)
    log["product"] = product
    sys.stderr.write(f"[product] {product}\n")
    time.sleep(1.0)

    # 공정 enum
    processes = enum_combo_fresh(get_main_win, "cb_process", args.limit_process, settle_per=1.0)
    sys.stderr.write(f"[processes] {len(processes)} found\n")
    for i, name in enumerate(processes):
        sys.stderr.write(f"  [{i}] {name}\n")

    # 각 공정 순회
    for proc_idx, proc_name in enumerate(processes):
        confirmed = select_by_index_fresh(get_main_win, "cb_process", proc_idx, settle=2.0)
        proc_log = {"index": proc_idx, "name": confirmed, "items": []}
        log["processes"].append(proc_log)
        sys.stderr.write(f"\n[proc {proc_idx+1}/{len(processes)}] {confirmed}\n")

        # 검사항목 enum
        items = enum_combo_fresh(get_main_win, "cb_item", args.limit_item, settle_per=0.5)
        sys.stderr.write(f"  items: {len(items)}\n")

        for item_idx, item_name in enumerate(items):
            select_by_index_fresh(get_main_win, "cb_item", item_idx, settle=0.8)
            time.sleep(0.3)
            grid = fresh_ctrl(get_main_win, "grid")
            spec_text = get_grid_first_row_spec(grid)
            kind, params = classify_spec(spec_text)
            item_log = {
                "index": item_idx, "name": item_name,
                "spec_text": spec_text, "kind": kind,
                "params": [list(p) for p in params] if params else None,
                "actions": [],
            }
            proc_log["items"].append(item_log)
            sys.stderr.write(f"    [{item_idx+1}] {item_name[:40]} | spec='{spec_text[:30]}' | kind={kind}\n")

            if args.mode == "enum-only":
                continue

            # ---- A/B 분기 입력 ----
            inner_log = {"actions": []}
            try:
                if kind == "A":
                    lo, hi, decimals = params[0]
                    v1 = gen_normal_in_range(lo, hi, decimals)
                    v2 = gen_normal_in_range(lo, hi, decimals)
                    v3 = gen_normal_in_range(lo, hi, decimals)
                    item_log["values"] = [v1, v2, v3]
                    set_input(fresh_ctrl(get_main_win, "txt_x1"), f"{v1:.{decimals}f}", "txt_x1", inner_log)
                    set_input(fresh_ctrl(get_main_win, "txt_x2"), f"{v2:.{decimals}f}", "txt_x2", inner_log)
                    set_input(fresh_ctrl(get_main_win, "txt_x3"), f"{v3:.{decimals}f}", "txt_x3", inner_log)
                else:  # B
                    clear_input(fresh_ctrl(get_main_win, "txt_x1"), "txt_x1", inner_log)
                    clear_input(fresh_ctrl(get_main_win, "txt_x2"), "txt_x2", inner_log)
                    clear_input(fresh_ctrl(get_main_win, "txt_x3"), "txt_x3", inner_log)

                toggle_ok_if_off(fresh_ctrl(get_main_win, "chk_ok_x1"), "chk_ok_x1", inner_log)
                toggle_ok_if_off(fresh_ctrl(get_main_win, "chk_ok_x2"), "chk_ok_x2", inner_log)
                toggle_ok_if_off(fresh_ctrl(get_main_win, "chk_ok_x3"), "chk_ok_x3", inner_log)

                item_log["actions"] = inner_log["actions"]
            except Exception as e:
                item_log["input_err"] = str(e)[:200]
                log["fail_count"] += 1
                sys.stderr.write(f"      [FAIL input] {e}\n")
                continue

            # 저장 분기
            should_save = False
            if args.mode == "commit-all":
                should_save = True
            elif args.mode == "commit-process" and proc_idx == 0:
                should_save = True
            elif args.mode == "commit-one" and proc_idx == 0 and item_idx == 0:
                should_save = True

            if should_save:
                try:
                    fresh_ctrl(get_main_win, "btn_save").click_input()
                    time.sleep(2.0)
                    msg = (fresh_ctrl(get_main_win, "lbl_msg").window_text() or "").strip()
                    item_log["save_msg"] = msg
                    if "OK" in msg or "성공" in msg:
                        item_log["save"] = True
                        log["save_count"] += 1
                        sys.stderr.write(f"      [save OK] {msg[:60]}\n")
                    else:
                        item_log["save"] = False
                        log["fail_count"] += 1
                        sys.stderr.write(f"      [save FAIL] {msg[:60]}\n")
                except Exception as e:
                    item_log["save_err"] = str(e)[:200]
                    log["fail_count"] += 1
                    sys.stderr.write(f"      [save EXC] {e}\n")
            else:
                item_log["save"] = "skipped"

    log["ok"] = (log["fail_count"] == 0)
    log["ts_end"] = datetime.now().isoformat()
    out = STATE_DIR / f"run_v21_{started:%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {out.name} mode={args.mode} processes={len(processes)} saves={log['save_count']} fails={log['fail_count']}")
    return 0 if log["ok"] else 3


if __name__ == "__main__":
    sys.exit(main())
