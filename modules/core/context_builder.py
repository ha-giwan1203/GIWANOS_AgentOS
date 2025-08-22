# [ACTIVE] VELOS 컨텍스트 빌더 - 세션 컨텍스트 관리 모듈
# VELOS 운영 철학 선언문: 파일명 절대 변경 금지. 수정 시 자가 검증 포함. 
# 실행 결과 기록. 경로/구조 불변. 실패는 로깅하고 자동 복구를 시도한다.
import os
import sys
import json
import time
from typing import List, Dict, Any, Optional

# 고정 경로 주입
ROOT = os.getenv("VELOS_ROOT", "/workspace")
if ROOT not in sys.path:
    sys.path.append(ROOT)

from modules.utils.memory_adapter import MemoryAdapter  # shim을 통한 import

HEALTH = os.path.join(ROOT, "data", "logs", "system_health.json")


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def build_context_block(
    limit: int = 50, hours: int = 24, required_tags: Optional[List[str]] = None
) -> str:
    """
    최근 N개 + 최근 H시간 내 기록을 혼합으로 끌어와 프롬프트 헤더 블록을 만든다.
    required_tags가 있으면 해당 태그 포함 항목을 우선 배치.
    """
    m = MemoryAdapter()
    moved = m.flush_jsonl_to_db()  # 세션 시작 시 누락된 append를 DB로 밀어넣기
    recent = m.recent(limit=limit)

    # 시간 윈도 필터
    now = int(time.time())
    cutoff = now - hours * 3600
    recent = [r for r in recent if int(r.get("ts", 0)) >= cutoff] or recent

    # 태그 가중 정렬
    if required_tags:

        def score(item):
            tags = set(item.get("tags") or [])
            inter = len(tags.intersection(required_tags))
            return (inter, item.get("ts", 0))

        recent.sort(key=score, reverse=True)
    else:
        recent.sort(key=lambda r: r.get("ts", 0), reverse=True)

    # 프롬프트 블록 조립
    lines = []
    lines.append("<<VELOS_CONTEXT:BEGIN>>")
    lines.append(
        f"migrated={moved} items; window={hours}h; "
        f"pulled={min(len(recent), limit)}"
    )
    for r in recent[:limit]:
        ts = r.get("ts", 0)
        role = r.get("from", "system")
        insight = (r.get("insight") or "").replace("\n", " ").strip()
        tags = ",".join(r.get("tags") or [])
        lines.append(f"[{ts}] ({role}) {insight} | tags={tags}")
    lines.append("<<VELOS_CONTEXT:END>>")
    block = "\n".join(lines)

    # 헬스 업데이트
    h = _read_json(HEALTH)
    h["context_build_last_ts"] = int(time.time())
    h["context_build_last_count"] = len(recent[:limit])
    h["context_build_last_ok"] = True
    _write_json(HEALTH, h)

    return block


if __name__ == "__main__":
    # 자가 검증 테스트
    print("=== VELOS Context Builder 자가 검증 테스트 ===")

    # 기본 컨텍스트 블록 생성
    context = build_context_block(limit=10, hours=24)
    print("생성된 컨텍스트 블록:")
    print(context)

    # 태그 필터링 테스트
    tagged_context = build_context_block(
        limit=5, hours=24, required_tags=["test"]
    )
    print("\n태그 필터링된 컨텍스트 블록:")
    print(tagged_context)

    # 헬스 로그 확인
    health = _read_json(HEALTH)
    print(
        f"\n헬스 로그 업데이트: "
        f"context_build_last_ok={health.get('context_build_last_ok')}"
    )

    print("=== 자가 검증 완료 ===")

