# [ACTIVE] VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.
# -*- coding: utf-8 -*-

# [ACTIVE] VELOS Reflection Risk Tagger
# - 자동 리스크 레벨 태깅 (HIGH/MED/LOW)
# - 최근성 40% + 키워드/시그널 60% 점수
# - 장애 징후, 보안, 데드라인 등 고위험 항목 탐지
#
# Usage:
#   python modules/automation/reflection_risk_tagger.py
#   python modules/automation/reflection_risk_tagger.py --include-reflections

from __future__ import annotations
import os
import re
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos"))
MEM = ROOT / "data" / "memory" / "learning_memory_cleaned.jsonl"
REF_DIR = ROOT / "data" / "reflections"
REPORTS = ROOT / "data" / "reports"

RISK_KEYWORDS = {
    "HIGH": [
        "outage", "downtime", "data loss", "leak", "credential", "secret",
        "prod incident", "deadline today", "security"
    ],
    "MED": [
        "retry storm", "latency", "throttle", "fallback", "degraded",
        "delay", "over budget", "overdue", "rollback"
    ],
    "LOW": ["refactor", "nit", "todo", "backlog", "someday"]
}
RISK_HINTS = re.compile(
    r"(?i)(error|fail|panic|exception|traceback|secrets?|token|apikey|"
    r"deadline|launch|prod|incident)"
)

def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _read_jsonl(p: Path) -> List[Dict[str, Any]]:
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not ln.strip():
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def _recency(ts: str | None) -> float:
    from datetime import datetime
    if not ts: return 0.4
    try:
        t = datetime.fromisoformat(ts.replace("Z",""))
        age = (time.time() - t.timestamp())/86400.0
        # 0d→1.0, 30d→~0.25
        import math
        return max(0.0, min(1.0, math.exp(-0.046*age)))
    except: return 0.4

def _kw_score(txt: str) -> tuple[float,str]:
    t = txt.lower()
    lvl = "LOW"; s=0.0
    if any(k in t for k in RISK_KEYWORDS["HIGH"]): lvl="HIGH"; s=0.9
    elif any(k in t for k in RISK_KEYWORDS["MED"]): lvl="MED"; s=0.6
    elif any(k in t for k in RISK_KEYWORDS["LOW"]): lvl="LOW"; s=0.3
    if RISK_HINTS.search(t): s = max(s, 0.7); lvl = "HIGH" if s>=0.8 else ("MED" if s>=0.5 else lvl)
    return s, lvl

def _tag(items: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    out=[]
    for r in items:
        text = (r.get("text") or r.get("content") or "").strip()
        if not text: continue
        rs = _recency(r.get("ts"))
        ks, lvl = _kw_score(text)
        score = round(0.4*rs + 0.6*ks, 4)
        out.append({
            "text": text,
            "ts": r.get("ts"),
            "source": r.get("source","memory"),
            "risk_level": "HIGH" if score>=0.75 else ("MED" if score>=0.45 else "LOW"),
            "score": score
        })
    out.sort(key=lambda x: (-x["score"], x.get("ts") or ""))
    return out

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-reflections", action="store_true", help="scan data/reflections/*.json also")
    args = parser.parse_args(argv)

    REPORTS.mkdir(parents=True, exist_ok=True)
    items = _read_jsonl(MEM)

    if args.include_reflections and REF_DIR.exists():
        for p in sorted(REF_DIR.glob("*.json")):
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                text = j.get("summary") or j.get("text") or ""
                items.append({"text": text, "ts": j.get("ts") or j.get("timestamp"), "source": "reflection"})
            except: pass

    tagged = _tag(items)
    # 상위만 요약
    top_high = [x for x in tagged if x["risk_level"]=="HIGH"][:20]
    rep = {
        "generated_at": _now(),
        "counts": {"total": len(tagged), "HIGH": sum(x["risk_level"]=="HIGH" for x in tagged),
                   "MED": sum(x["risk_level"]=="MED" for x in tagged), "LOW": sum(x["risk_level"]=="LOW" for x in tagged)},
        "top_high": top_high
    }
    (REPORTS/"reflection_risk_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    # md
    lines = [f"# Reflection Risk Report",
             f"- generated_at: {rep['generated_at']}",
             f"- total: {rep['counts']['total']} | HIGH: {rep['counts']['HIGH']} | MED: {rep['counts']['MED']} | LOW: {rep['counts']['LOW']}",
             "## Top HIGH (<=20)"]
    for r in top_high:
        lines.append(f"- [{r['score']:.2f}] {r.get('ts','')} | {r['source']} | {r['text'][:120]}")
    (REPORTS/"reflection_risk_report.md").write_text("\n".join(lines), encoding="utf-8")

    print("[OK] reflection risk report generated")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
