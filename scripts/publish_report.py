# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:\giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
"""
VELOS 보고서 퍼블리셔
- 타임스탬프 파일로 영구 보관: velos_report_YYYYMMDD_HHMMSS.pdf
- 업로드 편의를 위한 별칭: velos_report_latest.pdf (항상 덮어씀)
- 직전 업로드와 내용 동일하면 업로드 스킵(sha256)
"""

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

# 루트/경로
from modules.report_paths import ROOT

REPORT_DIR = ROOT / "data" / "reports"
ALIAS = REPORT_DIR / "velos_report_latest.pdf"
STATE_FILE = REPORT_DIR / ".last_upload.json"

# 통합전송 큐 생성 함수
def create_dispatch_message(file_path: Path, title: str) -> bool:
    """통합전송 시스템용 메시지 생성"""
    try:
        dispatch_queue = ROOT / "data" / "dispatch" / "_queue" 
        dispatch_queue.mkdir(parents=True, exist_ok=True)
        
        message = {
            "title": title,
            "message": f"📊 VELOS 보고서가 생성되었습니다.\n\n파일: {file_path.name}\n크기: {file_path.stat().st_size:,} bytes\n생성시간: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "file_path": str(file_path),
            "channels": {
                "slack": {
                    "enabled": True,
                    "channel": "#general",
                    "upload_file": True
                },
                "notion": {
                    "enabled": False
                }
            }
        }
        
        # 큐에 메시지 저장
        queue_file = dispatch_queue / f"report_publish_{time.strftime('%Y%m%d_%H%M%S')}.json"
        queue_file.write_text(json.dumps(message, ensure_ascii=False, indent=2), encoding="utf-8")
        
        print(f"[INFO] 통합전송 큐에 추가: {queue_file.name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 통합전송 큐 생성 실패: {e}")
        return False


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

    # 4) 통합전송 큐에 추가 (Bridge에게 위임)
    ok = create_dispatch_message(alias, f"VELOS Report - {alias.name}")
    if ok:
        save_state(
            {
                "sha256": cur_hash,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file": str(ts_file),
            }
        )
        print("[OK] 통합전송 큐 추가 완료 및 상태 저장")
        print("[INFO] Bridge 시스템이 자동으로 전송 처리할 예정")
        return 0
    else:
        print("[FAIL] 통합전송 큐 추가 실패")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
