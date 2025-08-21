# =========================================================
# VELOS 운영 철학 선언문
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
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import warnings
from datetime import datetime
from pathlib import Path

from modules.report_paths import ROOT, P

# fpdf 경고 소음 제거
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")
LOGS = ROOT / r"data\logs"
REPORTS = ROOT / r"data\reports"
MEMORY = ROOT / r"data\memory"
REFLECT = ROOT / r"data\reflections"
REPORTS.mkdir(parents=True, exist_ok=True)

API_COST = LOGS / "api_cost_log.json"
SYSTEM_HEALTH = LOGS / "system_health.json"
LEARNING_MEMORY = MEMORY / "learning_memory.json"
SUMMARY_MEMORY = MEMORY / "learning_summary.json"

FONT_CANDS = [
    (ROOT / r"fonts\Nanum_Gothic\NotoSansKR-Regular.ttf", "NotoSansKR"),
    (ROOT / r"fonts\Nanum_Gothic\NanumGothic-Regular.ttf", "Nanum"),
    (ROOT / r"fonts\Nanum_Gothic\NotoSansKR-Medium.ttf", "NotoSansKR"),
]


# ------------------ IO 유틸 ------------------
def jread(p: Path):
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return None


def recent_reflections(n=5):
    items = []
    if REFLECT.exists():
        files = sorted(REFLECT.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:n]
        for fp in files:
            data = jread(fp) or {}
            title = None
            for k in (
                "summary",
                "insight",
                "title",
                "message",
                "text",
                "content",
                "log",
            ):
                if isinstance(data, dict) and data.get(k):
                    title = str(data[k])
                    break
            if not title:
                title = fp.stem
            level = (
                isinstance(data, dict) and (data.get("level") or data.get("severity"))
            ) or "info"
            items.append({"file": fp.name, "title": title[:140], "level": level})
    return items


def summarise_cost(x):
    if not x:
        return dict(entries=0, sum_cost=0.0)
    if isinstance(x, dict) and "total_cost" in x:
        return dict(entries=int(x.get("entries", 0)), sum_cost=float(x.get("total_cost", 0)))
    if isinstance(x, dict) and isinstance(x.get("logs"), list):
        tot = 0.0
        for row in x["logs"]:
            with contextlib.suppress(Exception):
                tot += float(row.get("cost", 0))
        return dict(entries=len(x["logs"]), sum_cost=tot)
    if isinstance(x, list):
        tot = 0.0
        for row in x:
            with contextlib.suppress(Exception):
                tot += float(row.get("cost", 0))
        return dict(entries=len(x), sum_cost=tot)
    return dict(entries=0, sum_cost=0.0)


def fmt_uptime(sec):
    try:
        sec = int(sec)
        d, r = divmod(sec, 86400)
        h, r = divmod(r, 3600)
        m, _ = divmod(r, 60)
        parts = []
        if d:
            parts.append(f"{d}d")
        if h or d:
            parts.append(f"{h}h")
        parts.append(f"{m}m")
        return " ".join(parts)
    except Exception:
        return "N/A"


# ------------------ 본문 생성 ------------------
def build_markdown(now: datetime) -> str:
    health = jread(SYSTEM_HEALTH) or {}
    api = summarise_cost(jread(API_COST))
    mem_summary = jread(SUMMARY_MEMORY) or {}
    lm = jread(LEARNING_MEMORY)
    refs = recent_reflections(5)

    lines = []
    lines.append("# VELOS AI Insights Report")
    lines.append(f"생성시각: {now:%Y-%m-%d %H:%M:%S}")
    lines.append("")
    lines.append("## 1) 시스템 상태")
    status = (isinstance(health, dict) and (health.get("status") or health.get("overall"))) or "N/A"
    lines.append(f"- 상태: **{status}**")
    uptime = isinstance(health, dict) and health.get("uptime")
    lines.append(f'- Uptime: {fmt_uptime(uptime) if uptime else "N/A"}')
    alerts = isinstance(health, dict) and health.get("alerts")
    lines.append(f"- Alerts: {len(alerts) if isinstance(alerts, list) else 0}")

    lines.append("")
    lines.append("## 2) 메모리 요약")
    if hasattr(lm, "__len__"):
        lines.append(f"- learning_memory.json 키 수: {len(lm)}")
    brief = isinstance(mem_summary, dict) and mem_summary.get("summary")
    lines.append(f'- 최근 요약: {str(brief)[:180] if brief else "(요약 없음)"}')

    lines.append("")
    lines.append("## 3) API 비용 요약")
    lines.append(f'- 기록 수: {api["entries"]}')
    lines.append(f'- 총 비용(추정): {api["sum_cost"]:.6f}')

    lines.append("")
    lines.append("## 4) 최신 리플렉션 5개")
    if refs:
        for r in refs:
            lines.append(f'- [{r["level"]}] {r["title"]} ({r["file"]})')
    else:
        lines.append("- 리플렉션 파일 없음")

    lines.append("")
    lines.append("## 5) 생성 로그")
    lines.append(f"- 보고서 루트: {REPORTS}")
    return "\n".join(lines)


# ------------------ PDF ------------------
def pick_font():
    for p, fam in FONT_CANDS:
        if p.exists():
            return str(p), fam
    return None, None


def to_ascii(s: str) -> str:
    # fpdf가 라틴1만 허용하는 경우 대비
    try:
        return str(s).encode("latin-1", "ignore").decode("latin-1")
    except Exception:
        return str(s)


def build_pdf(pdf_path: Path, title: str, body: str) -> bool:
    try:
        from fpdf import FPDF
    except Exception as e:
        print("[WARN] fpdf2 로드 실패:", e)
        return False

    pdf = FPDF()
    pdf.add_page()

    # 좌우 마진을 넉넉히; width를 초과하는 긴 단어 대비
    pdf.set_margins(15, 15, 15)
    avail_w = pdf.w - pdf.l_margin - pdf.r_margin

    font_path, family = pick_font()
    if font_path:
        try:
            pdf.add_font(family, style="", fname=font_path, uni=True)
            pdf.set_font(family, size=16)
            pdf.multi_cell(avail_w, 8, txt=title)
            pdf.ln(2)
            pdf.set_font(family, size=10)
            pdf.multi_cell(avail_w, 5.5, txt=body)
        except Exception as e:
            print("[WARN] 한글 폰트 실패, ASCII로 대체:", e)
            pdf.set_font("Arial", size=16)
            pdf.multi_cell(avail_w, 8, txt=to_ascii(title))
            pdf.ln(2)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(avail_w, 5.5, txt=to_ascii(body))
    else:
        print("[WARN] 폰트 없음, ASCII 출력")
        pdf.set_font("Arial", size=16)
        pdf.multi_cell(avail_w, 8, txt=to_ascii(title))
        pdf.ln(2)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(avail_w, 5.5, txt=to_ascii(body))

    pdf.output(str(pdf_path))
    return True


# ------------------ 엔트리 ------------------
def main():
    now = datetime.now()
    md_text = build_markdown(now)  # <- 여기가 문제였던 부분(없어서 터짐)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    md_path = REPORTS / f"velos_report_{stamp}.md"
    pdf_path = REPORTS / f"velos_report_{stamp}.pdf"
    md_path.write_text(md_text, encoding="utf-8")

    title = f"VELOS AI Insights Report - {now:%Y-%m-%d %H:%M:%S}"
    ok_pdf = build_pdf(pdf_path, title, md_text)

    print("[OK] MD:", md_path)
    print(
        "[OK] PDF:" if ok_pdf else "[SKIP] PDF 생성 건너뜀 (fpdf2)",
        pdf_path if ok_pdf else "",
    )

    # 통합전송 시스템으로 자동 전송 (Bridge 위임)
    if os.environ.get("SLACK_AUTOSEND") in ("1", "true", "True") and ok_pdf:
        try:
            dispatch_queue = ROOT / "data" / "dispatch" / "_queue"
            dispatch_queue.mkdir(parents=True, exist_ok=True)
            
            message = {
                "title": "🤖 VELOS AI Insights Report",
                "message": f"📈 AI 인사이트 보고서가 생성되었습니다.\n\n파일: {pdf_path.name if pdf_path else 'N/A'}\n생성시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n🔍 주요 내용:\n- 시스템 건강 상태\n- API 비용 분석\n- 학습 메모리 요약\n- 성찰 데이터 분석",
                "file_path": str(pdf_path) if pdf_path else None,
                "channels": {
                    "slack": {
                        "enabled": True,
                        "channel": "#general",
                        "upload_file": True if pdf_path else False
                    }
                }
            }
            
            # 큐에 메시지 저장
            import time
            queue_file = dispatch_queue / f"ai_insights_{time.strftime('%Y%m%d_%H%M%S')}.json"
            queue_file.write_text(json.dumps(message, ensure_ascii=False, indent=2), encoding="utf-8")
            
            print(f"[INFO] 통합전송 큐에 추가: {queue_file.name}")
            
        except Exception as e:
            print(f"[WARN] 통합전송 큐 추가 실패: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
