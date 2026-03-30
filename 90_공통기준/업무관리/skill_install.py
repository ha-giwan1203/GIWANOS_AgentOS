"""
skill_install.py — Phase 6 스킬 자동 설치 훅
.skill 파일(ZIP) 변경 감지 시 Claude skills 디렉토리에 자동 압축 해제.

사용:
  - watch_changes.py Phase 6 훅으로 자동 호출
  - 단독 실행: python skill_install.py           (90_공통기준/스킬/*.skill 전체 재설치)
  - 단독 실행: python skill_install.py <path>    (특정 .skill 파일만)
"""

import sys
import zipfile
from pathlib import Path

# ── Claude skills 설치 디렉토리 탐색 ─────────────────────────────────────

def find_claude_skills_dir() -> Path | None:
    """AppData/Roaming/Claude 하위 skills 디렉토리를 동적으로 탐색."""
    base = Path.home() / "AppData/Roaming/Claude/local-agent-mode-sessions/skills-plugin"
    if not base.exists():
        return None
    dirs = sorted(base.glob("*/*/skills"), key=lambda p: p.stat().st_mtime, reverse=True)
    return dirs[0] if dirs else None


# ── 단일 스킬 설치 ────────────────────────────────────────────────────────

def install_skill(skill_path: Path, install_dir: Path, logger=None) -> bool:
    """
    단일 .skill(ZIP) 파일을 install_dir 에 압축 해제.
    ZIP 내부 구조: {skill-name}/SKILL.md → install_dir/{skill-name}/SKILL.md
    """
    try:
        if not zipfile.is_zipfile(skill_path):
            msg = f"[skill_install] ZIP 아님, 건너뜀: {skill_path.name}"
            _log(msg, logger, level="warning")
            return False
        with zipfile.ZipFile(skill_path, "r") as zf:
            zf.extractall(install_dir)
        _log(f"[skill_install] 설치 완료: {skill_path.name} → {install_dir}", logger)
        return True
    except Exception as e:
        _log(f"[skill_install] 실패: {skill_path.name} | {e}", logger, level="error")
        return False


def _log(msg, logger=None, level="info"):
    if logger:
        getattr(logger, level)(msg)
    else:
        print(msg)


# ── watch_changes.py Phase 6 훅 인터페이스 ───────────────────────────────

def process_events(ready: list, repo_root: str, dry_run: bool, logger=None) -> dict:
    """
    ready: list[(abs_path: str, entry: dict)]
    .skill 파일의 created / modified 이벤트만 처리.
    """
    install_dir = find_claude_skills_dir()
    if not install_dir:
        _log("[skill_install] Claude skills 디렉토리 없음 — 건너뜀", logger, "warning")
        return {"ok": False, "installed": []}

    installed = []
    for abs_path, entry in ready:
        p = Path(abs_path)
        if p.suffix.lower() != ".skill":
            continue
        if entry["event_type"] not in ("created", "modified"):
            continue
        if not p.exists():
            _log(f"[skill_install] 파일 없음, 건너뜀: {p.name}", logger, "warning")
            continue
        if dry_run:
            _log(f"[DRY-RUN] skill_install: {p.name} → {install_dir}", logger)
            installed.append(p.name)
        else:
            if install_skill(p, install_dir, logger):
                installed.append(p.name)

    return {"ok": len(installed) > 0, "installed": installed}


# ── 단독 실행 ─────────────────────────────────────────────────────────────

def main():
    install_dir = find_claude_skills_dir()
    if not install_dir:
        print("[ERROR] Claude skills 디렉토리를 찾을 수 없습니다.")
        sys.exit(1)

    if len(sys.argv) >= 2:
        # 특정 파일 지정
        targets = [Path(a) for a in sys.argv[1:]]
    else:
        # 전체 재설치
        src_dir = Path(__file__).parent.parent / "스킬"
        targets = list(src_dir.glob("*.skill"))

    if not targets:
        print("[INFO] 설치할 .skill 파일이 없습니다.")
        return

    ok = fail = 0
    for t in targets:
        if install_skill(t, install_dir):
            ok += 1
        else:
            fail += 1

    print(f"\n완료 — 성공: {ok}개 / 실패: {fail}개")
    print(f"설치 경로: {install_dir}")


if __name__ == "__main__":
    main()
