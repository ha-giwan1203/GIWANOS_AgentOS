# [ACTIVE] VELOS 운영 철학 선언문
# =========================================================
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=/home/user/webapp 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
# [ACTIVE] VELOS 운영: report_paths (호환 고정판)
# - 상단에서 ROOT, P를 반드시 내보냄 (legacy 코드 호환)

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

# 공통 유틸 가져오기
from modules.velos_common import ensure_dirs as _ensure_dirs
from modules.velos_common import env_presence as _env_presence
from modules.velos_common import paths as _paths

# --- Export: 레거시 호환 필수 심볼 ---
P: Dict[str, Path] = _paths()
ROOT: Path = P["ROOT"]
# -------------------------------------


def ensure_dirs() -> None:
    _ensure_dirs()


def env_presence(keys=("OPENAI_API_KEY", "NOTION_TOKEN", "SLACK_BOT_TOKEN")) -> Dict[str, str]:
    return _env_presence(keys)


def memory_file_ready() -> bool:
    mm = P["LEARNING_MEMORY"]
    if mm.exists():
        return True
    try:
        mm.write_text(
            json.dumps(
                {"meta": {"created_by": "report_paths.py", "version": 1}, "records": []},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


if __name__ == "__main__":
    ensure_dirs()
    ok = memory_file_ready()
    print("VELOS_ROOT=", ROOT)
    print("learning_memory.json=", "ok" if ok else "failed")
    print("env=", env_presence())
