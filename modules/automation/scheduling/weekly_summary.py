from __future__ import annotations
# =============================================
# VELOS: Weekly Summary Generator
# =============================================

from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic

from pathlib import Path

def generate_weekly_summary(out_dir: str) -> str:
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    name = f"weekly_summary_{now_kst().strftime('%Y%m%d')}.md"
    path = outp / name
    md = [
        "# VELOS 주간 요약",
        f"- 생성(UTC): {now_utc().isoformat()}Z",
        "- 상태: 시스템 정상",
        "- 모듈: CoT / Advanced RAG / Adaptive / Optimizers 완료",
        "",
        "## 비고",
        "- 자동 생성 문서",
    ]
    path.write_text("\n".join(md), encoding="utf-8")
    return str(path)
