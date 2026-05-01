"""SmartMES 잡셋업 — 공정·검사항목·검사 그리드 enum (read-only 탐색)

목적: v2.1 다중 공정/검사항목 순회 plan 작성을 위해 현 잡셋업 화면 데이터 구조 탐색.
  - cb_process 공정 N개 enum
  - 각 공정에 대해 cb_item 검사항목 M개 enum
  - 각 검사항목 선택 시 dgvJobSetup 그리드 컬럼·행 + 스펙 표시값 수집

❌ 입력·체크·저장 0건. 화면 select 만 사용.
✅ Phase 1 v2 검증과 동일한 안전 수준.

실행:
    python enum_processes_items.py [--limit-process N] [--limit-item N]
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from pywinauto import Application, Desktop
except ImportError:
    sys.stderr.write("pywinauto missing\n")
    sys.exit(2)


STATE_DIR = Path(__file__).parent.parent / "state"
STATE_DIR.mkdir(exist_ok=True)


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


def select_by_index(cb, idx):
    """ComboBox idx번째 항목 선택. HOME+DOWN×idx+ENTER (race 회피)."""
    cb.click_input()
    time.sleep(0.4)
    cb.type_keys("{HOME}", set_foreground=False)
    time.sleep(0.25)
    if idx > 0:
        cb.type_keys("{DOWN}" * idx, set_foreground=False)
        time.sleep(0.25)
    cb.type_keys("{ENTER}", set_foreground=False)
    time.sleep(0.6)
    return get_combo_value(cb)


def dump_grid(grid):
    """DataGridView 행 데이터 dump. UIA Table pattern."""
    rows = []
    try:
        # UIA Table 의 rows 는 children 중 DataItem 또는 Custom
        for row in grid.children():
            row_cells = []
            try:
                for cell in row.descendants():
                    try:
                        ct = cell.element_info.control_type
                        if ct in ("Text", "Edit", "Custom", "DataItem"):
                            t = (cell.window_text() or "").strip()
                            if t:
                                row_cells.append(t)
                    except Exception:
                        continue
            except Exception:
                pass
            if row_cells:
                rows.append(row_cells)
    except Exception as e:
        rows.append([f"<grid dump error: {e}>"])
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit-process", type=int, default=20)
    p.add_argument("--limit-item", type=int, default=20)
    args = p.parse_args()

    pid, title = find_main_pid()
    if not pid:
        print("[FAIL] SmartMES main window not found")
        return 1
    print(f"[connect] PID={pid} title='{title}'")

    app = Application(backend="uia").connect(process=pid)
    main_win = app.window(title_re=".*SAMSONG.*|.*SMART.*")

    # 메뉴 진입 보장
    try:
        menu = main_win.child_window(auto_id="btnMenuJobSetup", control_type="Button")
        menu.wait("exists", timeout=3)
        menu.click_input()
        time.sleep(1.5)
    except Exception as e:
        print(f"[FAIL] menu enter: {e}")
        return 2

    cb_product = main_win.child_window(auto_id="cbSchedule", control_type="ComboBox")
    cb_process = main_win.child_window(auto_id="cbProcess", control_type="ComboBox")
    cb_item = main_win.child_window(auto_id="cbJobSetup", control_type="ComboBox")
    grid = main_win.child_window(auto_id="dgvJobSetup", control_type="Table")
    cb_product.wait("exists", timeout=3)

    # 제품 첫 서열 선택
    product = select_by_index(cb_product, 0)
    print(f"[product] {product}")
    time.sleep(1.5)

    started = datetime.now()
    out_log = {
        "ts_start": started.isoformat(),
        "product": product,
        "processes": [],
    }

    # 공정 enum: 인덱스로 직접 이동, 마지막 항목 반복 시 break
    seen_processes = []
    for idx in range(args.limit_process):
        val = select_by_index(cb_process, idx)
        if not val:
            break
        if seen_processes and val == seen_processes[-1]:
            # DOWN이 더 이동 안 됨 (마지막 항목 도달)
            break
        seen_processes.append(val)
        print(f"  process[{idx}] = {val}")
        time.sleep(1.0)  # 검사항목 reload 대기

    print(f"[processes] {len(seen_processes)} found")

    # 각 공정에 대해 검사항목 enum + 그리드 dump
    for proc_idx, proc_name in enumerate(seen_processes):
        confirmed = select_by_index(cb_process, proc_idx)
        time.sleep(2.0)  # 검사항목 reload
        print(f"\n[{proc_idx+1}/{len(seen_processes)}] {confirmed}")

        proc_log = {"index": proc_idx, "name": confirmed, "items": []}

        # 검사항목 enum (인덱스 기반)
        seen_items = []
        for item_idx in range(args.limit_item):
            val = select_by_index(cb_item, item_idx)
            if not val:
                break
            if seen_items and val == seen_items[-1]:
                break
            seen_items.append(val)
            time.sleep(0.5)
        print(f"  items: {len(seen_items)}")

        # 각 검사항목 선택 후 grid dump
        for item_idx, item_name in enumerate(seen_items):
            select_by_index(cb_item, item_idx)
            time.sleep(0.7)
            grid_rows = dump_grid(grid)
            proc_log["items"].append({
                "index": item_idx,
                "name": item_name,
                "grid_rows": grid_rows,
            })
            print(f"    [{item_idx+1}] {item_name[:50]}  grid_rows={len(grid_rows)}")

        out_log["processes"].append(proc_log)

    out_log["ts_end"] = datetime.now().isoformat()
    out_path = STATE_DIR / f"enum_{started:%Y%m%d_%H%M%S}.json"
    out_path.write_text(json.dumps(out_log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[saved] {out_path}")

    # 요약
    total_items = sum(len(p["items"]) for p in out_log["processes"])
    print(f"\n=== SUMMARY ===")
    print(f"  processes: {len(out_log['processes'])}")
    print(f"  total items across all processes: {total_items}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
