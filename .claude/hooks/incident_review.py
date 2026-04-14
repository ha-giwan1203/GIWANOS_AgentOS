#!/usr/bin/env python3
"""incident_ledger.jsonl 빈도 분석 → 4갈래(+분류누락) 규칙 승격 제안.

세션40 학습 루프 완성 — 규칙 승격기.
GPT 토론 합의: (empty) → unclassified 별도 버킷, send_block은 문서보강 기본.

Usage:
  python3 .claude/hooks/incident_review.py                    # 기본 (7일, 임계치 5)
  python3 .claude/hooks/incident_review.py --days 30          # 30일 분석
  python3 .claude/hooks/incident_review.py --threshold 3      # 임계치 3
  python3 .claude/hooks/incident_review.py --json             # JSON 출력
  python3 .claude/hooks/incident_review.py --include-resolved # 해결 건 포함
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# incident_repair.py에서 load_jsonl 재사용
sys.path.insert(0, str(Path(__file__).parent))
try:
    from incident_repair import load_jsonl
except ImportError:
    def load_jsonl(path: str) -> list[dict[str, Any]]:
        """fallback: 직접 로드."""
        entries = []
        p = Path(path)
        if not p.exists():
            return entries
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries


# === 4갈래 + 분류누락 매핑 (세션40 GPT 토론 합의) ===
RECOMMENDATION_MAP: dict[str, str] = {
    # 규칙보강: hook 추가/강화 가능
    "pre_commit_check": "규칙보강",
    "evidence_missing": "규칙보강",
    "compile_fail": "규칙보강",
    "test_fail": "규칙보강",
    "task_consecutive_fail": "규칙보강",
    # 문서보강: CLAUDE.md/MEMORY 보강
    "harness_missing": "문서보강",
    "send_block": "문서보강",
    # 절차항목: 워크플로우 순서 변경
    "completion_before_git": "절차항목",
    "completion_before_state_sync": "절차항목",
    # 자동화불가: 이미 게이트됨, 인간 규율
    "scope_violation": "자동화불가",
    "dangerous_cmd": "자동화불가",
    "stop_guard_block": "자동화불가",
    # 기타
    "meta_drift": "절차항목",
    "structural_intermediate": "절차항목",
    # 세션45: 외부 피드백 소스
    "gpt_verdict": "문서보강",
    "user_correction": "규칙보강",
    # 세션45 C2: WARN 승격 분류
    "doc_drift": "문서보강",
    "python3_dependency": "규칙보강",
}

CATEGORY_DETAIL: dict[str, str] = {
    "규칙보강": "hook 추가/강화 또는 gate 조건 보강으로 자동 차단 가능",
    "문서보강": "CLAUDE.md, MEMORY, SKILL.md 등 지시문 보강으로 재발 방지",
    "절차항목": "워크플로우 순서/체크리스트 변경으로 누락 방지",
    "자동화불가": "이미 게이트됨. 인간 규율/습관 영역 — 자동화 추가 실익 낮음",
    "분류누락": "classification_reason 미부여. 먼저 분류 정규화 필요",
}

# classification → 제안 대상 경로 힌트
SUGGESTED_TARGETS: dict[str, str] = {
    "pre_commit_check": ".claude/hooks/final_check.sh 검사 항목 추가",
    "evidence_missing": ".claude/hooks/evidence_gate.sh 조건 보강",
    "compile_fail": "py_compile 검증 범위 확대",
    "test_fail": "smoke_test.sh / e2e_test.sh 시나리오 추가",
    "task_consecutive_fail": "해당 태스크 스크립트 안정성 점검",
    "harness_missing": "토론모드 CLAUDE.md 하네스 규칙 보강",
    "send_block": "send_gate 정책 또는 토론모드 지시문 보강",
    "completion_before_git": "완료 루틴에 git 상태 확인 단계 추가",
    "completion_before_state_sync": "완료 루틴에 TASKS/HANDOFF 갱신 강제",
    "scope_violation": "날짜 확인 습관 유지 (자동화 추가 실익 낮음)",
    "dangerous_cmd": "위험 명령 인식 유지 (이미 자동 차단됨)",
    "stop_guard_block": "독립 견해 포함 습관 유지",
    "meta_drift": "세션 종료 시 상태 문서 동기화 절차 보강",
    "structural_intermediate": "완료 루틴에서 TASKS/HANDOFF 갱신 순서 보강",
    # 세션45: 외부 피드백 소스
    "gpt_verdict": "GPT 지적 사항 기반 CLAUDE.md/SKILL.md 보강",
    "user_correction": "사용자 교정 패턴 분석 → hook/gate 자동화 검토",
    # 세션45 C2: WARN 승격 분류
    "doc_drift": "README/STATUS 문서 동기화 자동 강제 또는 hook sync 점검",
    "python3_dependency": "auto_compile.sh python3 의존 제거 또는 대체 정책 점검",
}


def parse_ts(ts_str: str) -> datetime | None:
    """ISO 8601 타임스탬프 파싱."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(ts_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def aggregate_frequency(
    entries: list[dict[str, Any]],
    days: int = 7,
    min_count: int = 5,
    include_resolved: bool = False,
    include_normal_flow: bool = False,
) -> list[dict[str, Any]]:
    """N일간 incident 빈도 집계. classification_reason 기준, 없으면 분류누락 버킷으로 집계."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    freq: dict[str, dict] = defaultdict(lambda: {"count": 0, "hooks": set(), "first_ts": None, "last_ts": None})

    for e in entries:
        if not include_resolved and e.get("resolved", False):
            continue
        # normal_flow 필터: 정상 안전장치 발화는 기본 제외
        if not include_normal_flow:
            if e.get("normal_flow", False):
                continue
            # structural_intermediate는 항상 정상 발화로 간주
            reason_check = (e.get("classification_reason") or "").strip()
            if reason_check == "structural_intermediate":
                continue
        ts = parse_ts(e.get("ts", ""))
        if ts is None or ts < cutoff:
            continue
        reason = (e.get("classification_reason") or "").strip()
        if not reason:
            reason = "__unclassified__"
        hook = e.get("hook", "")

        bucket = freq[reason]
        bucket["count"] += 1
        bucket["hooks"].add(hook)
        if bucket["first_ts"] is None or ts < bucket["first_ts"]:
            bucket["first_ts"] = ts
        if bucket["last_ts"] is None or ts > bucket["last_ts"]:
            bucket["last_ts"] = ts

    clusters = []
    for reason, data in freq.items():
        if data["count"] < min_count:
            continue
        clusters.append({
            "reason": reason,
            "hooks": sorted(data["hooks"]),
            "count": data["count"],
            "first_ts": data["first_ts"].isoformat() if data["first_ts"] else "",
            "last_ts": data["last_ts"].isoformat() if data["last_ts"] else "",
        })

    clusters.sort(key=lambda x: x["count"], reverse=True)
    return clusters


# === WARN 빈도 분석 (세션45 A1: 학습 루프 사각지대 해소) ===

def normalize_warn(raw: str) -> str:
    """WARN 문자열 정규화 — 숫자 차이를 무시하여 동일 패턴끼리 그룹화."""
    s = raw.strip().rstrip(";")
    if s.startswith("[WARN] "):
        s = s[7:]
    # 괄호 속 숫자 정규화: README(40) → README(N)
    s = re.sub(r"\(\d+\)", "(N)", s)
    # 날짜 정규화: STATUS(2026-04-11) → STATUS(DATE)
    s = re.sub(r"\(\d{4}-\d{2}-\d{2}\)", "(DATE)", s)
    return s.strip()


# WARN 패턴 → 승격 제안 매핑
WARN_PROMOTION_MAP: dict[str, dict[str, str]] = {
    "드리프트": {"candidate": True, "suggestion": "FAIL 승격 검토 (문서 동기화 자동 강제)"},
    "python3 의존": {"candidate": False, "suggestion": "규칙보강 검토 (auto_compile 정책 점검)"},
}


def aggregate_warn_frequency(
    entries: list[dict[str, Any]],
    days: int = 7,
    min_count: int = 1,
    include_resolved: bool = False,
    include_normal_flow: bool = False,
) -> list[dict[str, Any]]:
    """N일간 warn_keywords 개별 빈도 집계."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    freq: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "first_ts": None, "last_ts": None, "sample_raw": ""}
    )

    for e in entries:
        if not include_resolved and e.get("resolved", False):
            continue
        if not include_normal_flow:
            if e.get("normal_flow", False):
                continue
            reason_check = (e.get("classification_reason") or "").strip()
            if reason_check == "structural_intermediate":
                continue
        ts = parse_ts(e.get("ts", ""))
        if ts is None or ts < cutoff:
            continue
        wk = e.get("warn_keywords", "")
        if not wk:
            continue
        for w_raw in wk.split(";"):
            w_raw = w_raw.strip()
            if not w_raw:
                continue
            w_norm = normalize_warn(w_raw)
            if not w_norm:
                continue
            bucket = freq[w_norm]
            bucket["count"] += 1
            if not bucket["sample_raw"]:
                bucket["sample_raw"] = w_raw.strip()
            if bucket["first_ts"] is None or ts < bucket["first_ts"]:
                bucket["first_ts"] = ts
            if bucket["last_ts"] is None or ts > bucket["last_ts"]:
                bucket["last_ts"] = ts

    clusters = []
    for w_norm, data in freq.items():
        if data["count"] < min_count:
            continue
        # 승격 후보 판정
        promotion = {"candidate": False, "suggestion": "모니터링 유지 — 빈도 증가 시 FAIL 승격 검토"}
        for keyword, promo in WARN_PROMOTION_MAP.items():
            if keyword in w_norm:
                promotion = promo
                break
        clusters.append({
            "warn_type": w_norm,
            "count": data["count"],
            "first_ts": data["first_ts"].isoformat() if data["first_ts"] else "",
            "last_ts": data["last_ts"].isoformat() if data["last_ts"] else "",
            "sample_raw": data["sample_raw"],
            "promotion_candidate": promotion["candidate"],
            "suggestion": promotion["suggestion"],
        })

    clusters.sort(key=lambda x: x["count"], reverse=True)
    return clusters


def recommend_action(cluster: dict[str, Any]) -> dict[str, str]:
    """빈도 클러스터에 대한 4갈래 제안 생성."""
    reason = cluster["reason"]
    if reason == "__unclassified__":
        return {
            "category": "분류누락",
            "detail": CATEGORY_DETAIL["분류누락"],
            "target": "incident_ledger.jsonl 내 빈 classification_reason 항목 정규화",
        }
    category = RECOMMENDATION_MAP.get(reason, "문서보강")
    return {
        "category": category,
        "detail": CATEGORY_DETAIL.get(category, ""),
        "target": SUGGESTED_TARGETS.get(reason, "관련 hook/문서 확인"),
    }


def format_report(
    clusters: list[dict],
    recommendations: list[dict],
    days: int,
    threshold: int,
    as_json: bool = False,
    warn_clusters: list[dict] | None = None,
) -> str:
    if as_json:
        combined = []
        for c, r in zip(clusters, recommendations):
            combined.append({**c, "hooks": c["hooks"], **r})
        result = {"incidents": combined}
        if warn_clusters is not None:
            result["warn_analysis"] = warn_clusters
        return json.dumps(result, ensure_ascii=False, indent=2)

    lines = [f"=== Incident Review (최근 {days}일, 임계치 {threshold}건) ===", ""]
    if not clusters and not warn_clusters:
        lines.append("임계치 초과 항목 없음.")
        return "\n".join(lines)

    # 표 헤더
    lines.append(f"{'#':>3}  {'classification_reason':<35} {'건수':>5}  {'제안':<10} {'대상'}")
    lines.append("-" * 100)
    for i, (c, r) in enumerate(zip(clusters, recommendations), 1):
        reason_display = c["reason"] if c["reason"] != "__unclassified__" else "(빈 분류)"
        lines.append(f"{i:>3}  {reason_display:<35} {c['count']:>5}  {r['category']:<10} {r['target']}")

    lines.append("")
    lines.append("--- 상세 ---")
    for i, (c, r) in enumerate(zip(clusters, recommendations), 1):
        reason_display = c["reason"] if c["reason"] != "__unclassified__" else "(빈 분류)"
        lines.append(f"\n{i}. {reason_display} ({c['count']}건/{days}일) → {r['category']}")
        lines.append(f"   제안: {r['target']}")
        lines.append(f"   근거: {r['detail']}")
        lines.append(f"   관련 hook: {', '.join(c['hooks'])}")
        lines.append(f"   기간: {c['first_ts'][:10]} ~ {c['last_ts'][:10]}")

    # 카테고리별 합계
    lines.append("\n--- 카테고리 합계 ---")
    cat_counts: dict[str, int] = defaultdict(int)
    for r in recommendations:
        cat_counts[r["category"]] += 1
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {cat}: {cnt}건")

    # WARN 빈도 분석 섹션 (A1: 학습 루프 사각지대 해소)
    if warn_clusters:
        lines.append("")
        lines.append(f"=== WARN 빈도 분석 (최근 {days}일) ===")
        lines.append("")
        lines.append(f"{'#':>3}  {'warn_type':<45} {'건수':>5}  {'승격':>4}  {'제안'}")
        lines.append("-" * 110)
        for i, wc in enumerate(warn_clusters, 1):
            promo = "Yes" if wc["promotion_candidate"] else "No"
            lines.append(f"{i:>3}  {wc['warn_type']:<45} {wc['count']:>5}  {promo:>4}  {wc['suggestion']}")
        total_warns = sum(wc["count"] for wc in warn_clusters)
        promo_count = sum(1 for wc in warn_clusters if wc["promotion_candidate"])
        lines.append(f"\n  총 WARN: {total_warns}건, 승격 후보: {promo_count}건")

    return "\n".join(lines)


def main():
    # Windows cp949 인코딩 문제 방지
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="incident_ledger 빈도 분석 → 규칙 승격 제안")
    parser.add_argument("--ledger", type=str, default=".claude/incident_ledger.jsonl", help="incident ledger 경로")
    parser.add_argument("--days", type=int, default=7, help="분석 기간 (일)")
    parser.add_argument("--threshold", type=int, default=5, help="최소 빈도 임계치")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--include-resolved", action="store_true", help="해결 건 포함")
    parser.add_argument("--include-normal-flow", action="store_true", help="정상 안전장치 발화(normal_flow=true) 포함 (기본: 제외)")
    parser.add_argument("--no-warns", action="store_true", help="WARN 빈도 분석 섹션 생략")
    args = parser.parse_args()

    ledger_path = args.ledger
    if not Path(ledger_path).exists():
        print(f"ERROR: ledger 없음: {ledger_path}", file=sys.stderr)
        sys.exit(1)

    entries = load_jsonl(Path(ledger_path))
    clusters = aggregate_frequency(entries, days=args.days, min_count=args.threshold,
                                   include_resolved=args.include_resolved,
                                   include_normal_flow=args.include_normal_flow)
    recommendations = [recommend_action(c) for c in clusters]

    # WARN 빈도 분석 (A1: 학습 루프 사각지대 해소)
    warn_clusters = None
    if not args.no_warns:
        warn_min = max(1, args.threshold // 2)
        warn_clusters = aggregate_warn_frequency(
            entries, days=args.days, min_count=warn_min,
            include_resolved=args.include_resolved,
            include_normal_flow=args.include_normal_flow,
        )

    print(format_report(clusters, recommendations, args.days, args.threshold,
                        as_json=args.json, warn_clusters=warn_clusters))


if __name__ == "__main__":
    main()
