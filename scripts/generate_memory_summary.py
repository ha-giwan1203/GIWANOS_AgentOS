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

import contextlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from modules.report_paths import ROOT
MEM = ROOT / r"data\memory"
MEM.mkdir(parents=True, exist_ok=True)

REP_FIELDS = (
    "summary",
    "insight",
    "title",
    "name",
    "topic",
    "key",
    "id",
    "label",
    "text",
    "message",
    "content",
)


def _read_json(p: Path):
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return None


def _read_jsonl(p: Path, limit=300):
    out = []
    if not p.exists():
        return out
    try:
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
            line = line.strip()
            if not line:
                continue
            with contextlib.suppress(Exception):
                out.append(json.loads(line))
    except Exception:
        pass
    return out


def _clamp(s, n=48):
    s = str(s).replace("\\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _pick_repr(d: dict):
    for f in REP_FIELDS:
        v = d.get(f)
        if v:
            return _clamp(v)
    for v in d.values():
        if isinstance(v, str) and v.strip():
            return _clamp(v)
    return None


def _collect(obj, reps, total, max_reps):
    if isinstance(obj, dict):
        total += len(obj)
        reps.extend(list(obj.keys())[: max_reps - len(reps)])
    elif isinstance(obj, list):
        total += len(obj)
        for it in obj:
            if len(reps) >= max_reps:
                break
            s = _pick_repr(it) if isinstance(it, dict) else _clamp(it)
            if s:
                reps.append(s)
    return reps, total


def main():
    lm = _read_json(MEM / "learning_memory.json")
    dm = _read_json(MEM / "dialog_memory.json")
    inbox = _read_jsonl(MEM / "autosave_inbox.jsonl", limit=300)

    reps = []
    total = 0
    for src in (lm, dm, inbox):
        reps, total = _collect(src, reps, total, max_reps=12)

    summary = (
        "메모리 변경 없음 또는 소스 비어 있음."
        if not reps
        else f"최근 메모리 항목 {total}개 중 대표: " + ", ".join(reps[:12])
    )

    out = {
        "summary": summary,
        "count": total,
        "sources": {
            "learning_memory.json": (len(lm) if hasattr(lm, "__len__") else 0)
            if lm is not None
            else 0,
            "dialog_memory.json": (len(dm) if hasattr(dm, "__len__") else 0)
            if dm is not None
            else 0,
            "autosave_inbox.jsonl": len(inbox),
        },
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    # 원자적 저장: 임시파일에 쓰고 교체
    target = MEM / "learning_summary.json"
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(MEM)) as tf:
        json.dump(out, tf, ensure_ascii=False, indent=2)
        tmpname = tf.name
    os.replace(tmpname, target)
    print("[OK] learning_summary.json 갱신:", out["timestamp"])


if __name__ == "__main__":
    main()
