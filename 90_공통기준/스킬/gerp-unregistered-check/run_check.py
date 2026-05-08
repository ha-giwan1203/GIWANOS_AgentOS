"""
GERP 미등록 품번 확인 스킬 — 진입점 (run_check.py).

사용법:
    python run_check.py {MM} [--force]

    MM: 정산 대상 월 (01~12)
    --force: VALUES 사본 강제 재생성 (이미 있어도 덮어씀)

자동 흐름:
    1. 본체 경로 자동 탐색 (05_생산실적/조립비정산/{MM+1}월/정산_수식버전_{MM}월.xlsx)
    2. 작업 폴더 생성 (05_생산실적/조립비정산/{MM+1}월/오류리스트_재검증_{YYYYMMDD}/)
    3. 본체 → VALUES.xlsx 복사
    4. convert_to_values.py 실행 (수식 → 값)
    5. verify_error_labels.py 실행 (재검증 + 산출)
    6. 결과 요약 출력
"""
import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]  # 90_공통기준/스킬/gerp-unregistered-check → 업무리스트


def find_master(mm: str) -> Path:
    """본체 경로 자동 탐색. {MM+1}월 폴더 우선, fallback {MM}월 폴더."""
    mm_int = int(mm)
    candidates = [
        REPO_ROOT / "05_생산실적" / "조립비정산" / f"{mm_int+1:02d}월" / f"정산_수식버전_{mm_int:02d}월.xlsx",
        REPO_ROOT / "05_생산실적" / "조립비정산" / f"{mm_int:02d}월" / f"정산_수식버전_{mm_int:02d}월.xlsx",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"본체 파일 없음. 탐색: {candidates}")


def is_locked(p: Path) -> bool:
    lock = p.parent / f"~${p.name}"
    return lock.exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("month", help="정산 대상 월 (01~12)")
    ap.add_argument("--force", action="store_true", help="VALUES 사본 강제 재생성")
    args = ap.parse_args()

    mm = f'{int(args.month):02d}'
    print(f"[GERP 미등록 품번 확인] {mm}월 정산")

    # 1. 본체 탐색
    try:
        master = find_master(mm)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    print(f"  본체: {master}")

    if is_locked(master):
        print(f"[ERROR] 본체 락 — 사용자 Excel에서 닫고 다시 실행")
        sys.exit(2)

    # 2. 작업 폴더 — 정산 도메인 작업폴더(05_생산실적/조립비정산/{MM+1}월/) 안에 생성
    today = dt.datetime.now().strftime("%Y%m%d")
    settle_month_dir = REPO_ROOT / "05_생산실적" / "조립비정산" / f"{int(mm)+1:02d}월"
    work_dir = settle_month_dir / f"오류리스트_재검증_{today}"
    work_dir.mkdir(parents=True, exist_ok=True)
    values_path = work_dir / f"정산_수식버전_{mm}월_VALUES.xlsx"
    print(f"  작업 폴더: {work_dir}")

    # 3. 복사
    if values_path.exists() and not args.force:
        print(f"  VALUES 사본 존재 — 스킵 (--force로 재생성)")
    else:
        shutil.copy(master, values_path)
        print(f"  복사: {values_path.name}")

        # 4. 값 변환
        print("\n[Phase A] 수식 → 값 변환...")
        rc = subprocess.call(
            [sys.executable, str(SCRIPT_DIR / "convert_to_values.py"), str(values_path)],
        )
        if rc != 0:
            print(f"[ERROR] 값 변환 실패 rc={rc}")
            sys.exit(3)

    # 5. 재검증
    print("\n[Phase B+C+D] 재검증 + 산출...")
    rc = subprocess.call(
        [sys.executable, str(SCRIPT_DIR / "verify_error_labels.py"),
         "--values", str(values_path),
         "--out", str(work_dir),
         "--month", mm],
    )
    if rc != 0:
        print(f"[ERROR] 재검증 실패 rc={rc}")
        sys.exit(4)

    # 6. 결과 요약
    summary = work_dir / "verify_summary.md"
    if summary.exists():
        print(f"\n[DONE] 산출물: {work_dir}")
        print(f"  verify_summary.md / mismatch_rows.xlsx / category_distribution.csv / vendor_analysis.csv")
        print(f"\n사용자에게 verify_summary.md 공유 → ERP 정정 진행")


if __name__ == "__main__":
    main()
