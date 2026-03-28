# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

import os
import sys
import json
import time
from typing import List, Dict, Any

# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import get_velos_root, get_data_path, get_config_path, get_db_path
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root(): return "C:/giwanos"
    def get_data_path(*parts): return os.path.join("C:/giwanos", "data", *parts)
    def get_config_path(*parts): return os.path.join("C:/giwanos", "configs", *parts)
    def get_db_path(): return "C:/giwanos/data/memory/velos.db"

ROOT = get_velos_root() if "get_velos_root" in locals() else "C:/giwanos"
if ROOT not in sys.path:
    sys.path.append(ROOT)

HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")
HOTBUF = os.path.join(ROOT, "data", "memory", "hot_context.json")
os.makedirs(os.path.dirname(HOTBUF), exist_ok=True)

# 의존: memory_adapter / memory_reader (이미 이전 단계에서 넣음)
from modules.core.memory_adapter import MemoryAdapter
try:
    from modules.core.memory_reader import build_context_block
except Exception:
    # 최소한의 호환: build_context_block 없이도 동작
    def build_context_block(limit=50, hours=24, required_tags=None) -> str:
        m = MemoryAdapter()
        m.flush_jsonl_to_db()
        rows = m.recent(limit=limit)
        now = int(time.time())
        cutoff = now - hours*3600
        rows = [r for r in rows if r.get("ts", 0) >= cutoff] or rows
        lines = ["<<VELOS_CONTEXT:BEGIN>>", f"window={hours}h; pulled={len(rows[:limit])}"]
        for r in rows[:limit]:
            tags = ",".join(r.get("tags") or [])
            lines.append(f"[{r.get('ts',0)}] ({r.get('from','system')}) {r.get('insight','').strip()} | tags={tags}")
        lines.append("<<VELOS_CONTEXT:END>>")
        return "\n".join(lines)

REQUIRED_TAGS = ["명령","기억_유지","파일명_금지","운영_철학"]
TTL_SEC = 2 * 3600  # 핫버퍼 유효시간 2시간

def _read_json(p: str) -> Dict[str, Any]:
    """JSON 파일 안전 읽기"""
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_json(p: str, obj: Dict[str, Any]):
    """JSON 파일 안전 쓰기 (원자적 연산)"""
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)

def extract_mandates_from_block(block: str) -> Dict[str, Any]:
    """
    컨텍스트 블록에서 '명령'/'운영 철학'류를 추려서 강제 규칙 세트로 만든다.
    너무 똑똑할 필요 없다. 태그/키워드 기반 간단 파서.
    """
    mandates = {
        "FILE_NAMES_IMMUTABLE": True,
        "NO_FAKE_CODE": True,
        "ROOT_FIXED": "C:/giwanos",
        "SELF_TEST_REQUIRED": True,
        "PROMPT_ALWAYS_INCLUDE_CONTEXT": True,
    }

    if "파일명" in block and "금지" in block:
        mandates["FILE_NAMES_IMMUTABLE"] = True
    if "거짓" in block and "코드" in block:
        mandates["NO_FAKE_CODE"] = True
    if "운영 철학" in block:
        mandates["SELF_TEST_REQUIRED"] = True
    if "자가 검증" in block:
        mandates["SELF_TEST_REQUIRED"] = True
    if "경로 고정" in block:
        mandates["ROOT_FIXED"] = "C:/giwanos"
    if "컨텍스트" in block and "포함" in block:
        mandates["PROMPT_ALWAYS_INCLUDE_CONTEXT"] = True

    return mandates

def rebuild_hotbuf() -> Dict[str, Any]:
    """핫버퍼 재구성"""
    try:
        # 1) 새 컨텍스트 블록 생성
        ctx = build_context_block(limit=60, hours=48, required_tags=REQUIRED_TAGS)

        # 2) 강제 규칙 추출
        mandates = extract_mandates_from_block(ctx)

        # 3) 핫버퍼 구성
        payload = {
            "created_ts": int(time.time()),
            "ttl_sec": TTL_SEC,
            "context_block": ctx,
            "mandates": mandates,
            "rebuild_reason": "manual_rebuild"
        }

        _write_json(HOTBUF, payload)

        # 헬스 기록
        h = _read_json(HEALTH)
        h["hotbuf_last_build_ts"] = payload["created_ts"]
        h["hotbuf_ttl_sec"] = TTL_SEC
        h["hotbuf_ok"] = True
        h["hotbuf_rebuild_count"] = h.get("hotbuf_rebuild_count", 0) + 1
        _write_json(HEALTH, h)

        return payload

    except Exception as e:
        # 실패 시 기본값 반환
        return {
            "created_ts": int(time.time()),
            "ttl_sec": TTL_SEC,
            "context_block": "<<VELOS_CONTEXT:BEGIN>>\n[ERROR] Context build failed\n<<VELOS_CONTEXT:END>>",
            "mandates": {
                "FILE_NAMES_IMMUTABLE": True,
                "NO_FAKE_CODE": True,
                "ROOT_FIXED": "C:/giwanos",
                "SELF_TEST_REQUIRED": True,
                "PROMPT_ALWAYS_INCLUDE_CONTEXT": True,
            },
            "error": str(e)
        }

def load_hotbuf() -> Dict[str, Any]:
    """핫버퍼 로드 (만료 시 자동 재구성)"""
    try:
        buf = _read_json(HOTBUF)
        now = int(time.time())

        # 버퍼가 없거나 만료된 경우 재구성
        if not buf or now - int(buf.get("created_ts", 0)) > int(buf.get("ttl_sec", TTL_SEC)):
            return rebuild_hotbuf()

        return buf

    except Exception as e:
        # 로드 실패 시 재구성
        return rebuild_hotbuf()

def session_bootstrap() -> Dict[str, Any]:
    """
    세션 시작 시 반드시 호출:
    - JSONL→DB 플러시
    - 컨텍스트 블록 확보
    - 강제 규칙 확보
    - 핫버퍼 갱신/로딩
    """
    try:
        m = MemoryAdapter()
        moved = m.flush_jsonl_to_db()
        buf = load_hotbuf()

        # 헬스 반영
        h = _read_json(HEALTH)
        h["session_bootstrap_ts"] = int(time.time())
        h["session_bootstrap_flush_moved"] = moved
        h["session_bootstrap_ok"] = True
        h["session_bootstrap_count"] = h.get("session_bootstrap_count", 0) + 1
        _write_json(HEALTH, h)

        return buf  # {"context_block":..., "mandates":...}

    except Exception as e:
        # 부트스트랩 실패 시 기본값 반환
        return {
            "created_ts": int(time.time()),
            "ttl_sec": TTL_SEC,
            "context_block": "<<VELOS_CONTEXT:BEGIN>>\n[ERROR] Bootstrap failed\n<<VELOS_CONTEXT:END>>",
            "mandates": {
                "FILE_NAMES_IMMUTABLE": True,
                "NO_FAKE_CODE": True,
                "ROOT_FIXED": "C:/giwanos",
                "SELF_TEST_REQUIRED": True,
                "PROMPT_ALWAYS_INCLUDE_CONTEXT": True,
            },
            "error": str(e)
        }

def get_mandates() -> Dict[str, Any]:
    """현재 강제 규칙 반환"""
    buf = load_hotbuf()
    return buf.get("mandates", {})

def get_context_block() -> str:
    """현재 컨텍스트 블록 반환"""
    buf = load_hotbuf()
    return buf.get("context_block", "<<VELOS_CONTEXT:BEGIN>>\n[ERROR] No context\n<<VELOS_CONTEXT:END>>")

def force_rebuild():
    """핫버퍼 강제 재구성"""
    return rebuild_hotbuf()

def get_hotbuf_status() -> Dict[str, Any]:
    """핫버퍼 상태 정보 반환"""
    try:
        buf = _read_json(HOTBUF)
        now = int(time.time())

        if not buf:
            return {
                "exists": False,
                "age_sec": None,
                "expired": True,
                "ttl_sec": TTL_SEC
            }

        age_sec = now - int(buf.get("created_ts", 0))
        expired = age_sec > int(buf.get("ttl_sec", TTL_SEC))

        return {
            "exists": True,
            "age_sec": age_sec,
            "expired": expired,
            "ttl_sec": buf.get("ttl_sec", TTL_SEC),
            "created_ts": buf.get("created_ts"),
            "mandates_count": len(buf.get("mandates", {})),
            "context_length": len(buf.get("context_block", ""))
        }

    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }
