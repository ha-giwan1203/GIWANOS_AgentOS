"""
VELOS 보고서 퍼블리셔
- 타임스탬프 파일로 영구 보관: velos_report_YYYYMMDD_HHMMSS.pdf
- 업로드 편의를 위한 별칭: velos_report_latest.pdf (항상 덮어씀)
- 직전 업로드와 내용 동일하면 업로드 스킵(sha256)
"""

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

# 루트/경로
ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos"))
REPORT_DIR = ROOT / "data" / "reports"
ALIAS = REPORT_DIR / "velos_report_latest.pdf"
STATE_FILE = REPORT_DIR / ".last_upload.json"

# 업로드 함수 (이미 너희 쪽에 존재)
from scripts.notify_slack_api import send_report  # noqa: E402


def nowstamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(d: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_timestamped(src: Path) -> Path:
    """src를 보고서 폴더의 타임스탬프 파일로 보관하여 경로 반환"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    # 이미 우리의 규칙대로 저장돼 있으면 그대로 사용
    if (
        src.parent == REPORT_DIR
        and src.name.startswith("velos_report_")
        and src.suffix.lower() == ".pdf"
        and src.name != ALIAS.name
    ):
        return src
    # 아니면 타임스탬프 파일로 복사
    dst = REPORT_DIR / f"velos_report_{nowstamp()}.pdf"
    shutil.copy2(src, dst)
    return dst


def make_alias(ts_file: Path) -> Path:
    """latest 별칭 갱신"""
    shutil.copy2(ts_file, ALIAS)
    return ALIAS


def pick_latest_timestamped() -> Path | None:
    if not REPORT_DIR.exists():
        return None
    cands = [p for p in REPORT_DIR.glob("velos_report_*.pdf") if p.name != ALIAS.name]
    if not cands:
        return None
    return max(cands, key=lambda x: x.stat().st_mtime)


def main(argv):
    # 1) 소스 선택: 인자 경로 있으면 사용, 없으면 폴더에서 최신
    src: Path | None = None
    if len(argv) >= 2:
        src = Path(argv[1])
        if not src.exists():
            print(f"[ERROR] 소스 파일 없음: {src}")
            return 1
    else:
        src = pick_latest_timestamped()
        if src is None:
            print("[ERROR] 처리할 보고서가 없습니다.")
            return 1

    # 2) 타임스탬프 파일 보관 + 별칭 갱신
    ts_file = ensure_timestamped(src)
    alias = make_alias(ts_file)
    print(f"[INFO] 보관: {ts_file.name}")
    print(f"[INFO] 별칭 갱신: {alias.name} → {alias.stat().st_size} bytes")

    # 3) 중복 업로드 방지
    cur_hash = sha256(alias)
    st = load_state()
    if st.get("sha256") == cur_hash:
        print("[SKIP] 내용 동일 → 업로드 생략")
        return 0

    # 4) 업로드
    ok = send_report(alias, title=f"VELOS Report - {alias.name}")
    if ok:
        save_state(
            {
                "sha256": cur_hash,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file": str(ts_file),
            }
        )
        print("[OK] 업로드 완료 및 상태 저장")
        return 0
    else:
        print("[FAIL] 업로드 실패")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
