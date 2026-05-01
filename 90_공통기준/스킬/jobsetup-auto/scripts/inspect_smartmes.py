"""SmartMES mesclient.exe UI 컨트롤 트리 inspect (pywinauto PoC)

목적:
- 잡셋업 화면 컨트롤이 UIA(UI Automation) backend로 식별 가능한지 확인
- 가능하면 좌표 의존성 제거 가능 → PoC plan 작성 근거 확보
- 불가능하면 win32 backend, 그것도 안 되면 좌표 자동화 유지

실행:
    python inspect_smartmes.py [--backend uia|win32] [--depth 4]

사전 조건:
- mesclient.exe 실행 중이고 잡셋업 화면이 띄워진 상태
"""
import argparse
import sys
import time
from pathlib import Path

try:
    from pywinauto import Application, Desktop
except ImportError:
    sys.stderr.write("pywinauto 미설치 - pip install pywinauto\n")
    sys.exit(2)


def list_smartmes_windows(backend):
    """SmartMES 창 후보 나열."""
    desktop = Desktop(backend=backend)
    windows = desktop.windows()
    cands = []
    for w in windows:
        try:
            title = w.window_text() or ""
            cls = w.class_name() or ""
            proc = w.process_id()
            if "MES" in title.upper() or "SAMSONG" in title.upper() or "SMART" in title.upper():
                cands.append((title, cls, proc))
        except Exception:
            pass
    return cands


def dump_tree(elem, depth, max_depth, indent=0, out=None):
    """컨트롤 트리 재귀 dump."""
    if depth > max_depth:
        return
    try:
        title = (elem.window_text() or "")[:60]
        cls = elem.class_name() or ""
        ctrl_type = ""
        try:
            ctrl_type = elem.element_info.control_type or ""
        except Exception:
            pass
        auto_id = ""
        try:
            auto_id = elem.element_info.automation_id or ""
        except Exception:
            pass

        rect = ""
        try:
            r = elem.rectangle()
            rect = f" rect=({r.left},{r.top},{r.right},{r.bottom})"
        except Exception:
            pass

        line = f"{'  ' * indent}[{ctrl_type or cls}] '{title}' auto_id='{auto_id}'{rect}"
        print(line)
        if out is not None:
            out.append(line)

        for child in elem.children():
            dump_tree(child, depth + 1, max_depth, indent + 1, out)
    except Exception as e:
        msg = f"{'  ' * indent}<error reading: {e}>"
        print(msg)
        if out is not None:
            out.append(msg)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=["uia", "win32"], default="uia")
    p.add_argument("--depth", type=int, default=4)
    p.add_argument("--save", action="store_true", help="state/ 에 dump 저장")
    args = p.parse_args()

    print(f"=== SmartMES inspect (backend={args.backend}, depth={args.depth}) ===\n")

    cands = list_smartmes_windows(args.backend)
    if not cands:
        print("[FAIL] SmartMES 후보 창 없음. mesclient.exe 실행 + 잡셋업 화면 띄운 뒤 재실행.")
        return 1

    print("후보 창:")
    for title, cls, proc in cands:
        print(f"  PID={proc}  class='{cls}'  title='{title}'")

    # 첫 번째 후보 사용
    target_title, target_cls, target_pid = cands[0]
    print(f"\n[selected] PID={target_pid} title='{target_title}'\n")

    app = Application(backend=args.backend).connect(process=target_pid)
    main_win = app.window(title_re=".*SAMSONG.*|.*SMART.*|.*MES.*")
    out_lines = []
    print("--- 컨트롤 트리 ---")
    dump_tree(main_win, 0, args.depth, 0, out_lines)

    if args.save:
        state_dir = Path(__file__).parent.parent / "state"
        state_dir.mkdir(exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = state_dir / f"inspect_{args.backend}_{ts}.txt"
        out_path.write_text("\n".join(out_lines), encoding="utf-8")
        print(f"\n[saved] {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
