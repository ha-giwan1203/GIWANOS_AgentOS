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
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from modules.report_paths import ROOT
REFLECT = ROOT / r"data\reflections"
OUTIDX = REFLECT / "reflections_index.json"

# 요약에 쓸 후보 필드들(우선순위)
TEXT_FIELDS = (
    "summary",
    "title",
    "message",
    "text",
    "content",
    "insight",
    "log",
    "details",
    "note",
    "body",
)

LEVEL_PATTERNS = [
    ("error", re.compile(r"\b(error|exception|traceback|fail(ed)?|critical)\b", re.I)),
    ("warn", re.compile(r"\b(warn|warning|degraded|retry|timeout|latency)\b", re.I)),
    ("info", re.compile(r".*", re.S)),  # 기본값
]


def _load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _pick_text(d: dict) -> str | None:
    for k in TEXT_FIELDS:
        v = d.get(k)
        if v:
            return str(v)
    # dict 전체에서 문자열 값 아무거나
    for v in d.values():
        if isinstance(v, str) and v.strip():
            return v
    return None


def _one_liner(s: str, limit=140) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _classify(s: str) -> str:
    for lvl, pat in LEVEL_PATTERNS:
        if pat.search(s or ""):
            return lvl
    return "info"


def normalize_file(p: Path) -> dict | None:
    d = _load_json(p)
    if not isinstance(d, dict):
        d = {"raw": d}
    text = _pick_text(d) or p.stem
    d["summary"] = d.get("summary") or _one_liner(text)
    d["level"] = d.get("level") or _classify(text)
    d["source_file"] = p.name
    d["normalized_at"] = datetime.now().isoformat(timespec="seconds")
    # 원본은 보존하고, *_norm.json 으로 출력
    out = p.with_name(p.stem + "_norm.json")
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    # mtime을 최신으로 만들기 위해 한 번 더 씀
    out.touch()
    return {"file": out.name, "title": d["summary"], "level": d["level"]}


def main():
    REFLECT.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(REFLECT.glob("*.json")):
        # 이미 _norm.json 인 파일은 건너뛴다
        if p.name.endswith("_norm.json"):
            continue
        try:
            rec = normalize_file(p)
            if rec:
                items.append(rec)
        except Exception as e:
            items.append({"file": p.name, "title": f"normalize failed: {e}", "level": "warn"})
    # 최신 20개 인덱스
    OUTIDX.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "items": items[-20:],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[OK] normalized {len(items)} reflections, index written:", OUTIDX)


if __name__ == "__main__":
    main()
