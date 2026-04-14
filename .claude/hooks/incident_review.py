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
) -> list[dict[str, Any]]:
    """N일간 incident 빈도 집계. classification_reason 기준, 없으면 분류누락 버킷으로 집계."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    freq: dict[str, dict] = defaultdict(lambda: {"count": 0, "hooks": set(), "first_ts": None, "last_ts": None})

    for e in entries:
        if not include_resolved and e.get("resolved", False):
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
) -> str:
    if as_json:
        combined = []
        for c, r in zip(clusters, recommendations):
            combined.append({**c, "hooks": c["hooks"], **r})
        return json.dumps(combined, ensure_ascii=False, indent=2)

    lines = [f"=== Incident Review (최근 {days}일, 임계치 {threshold}건) ===", ""]
    if not clusters:
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
    args = parser.parse_args()

    ledger_path = args.ledger
    if not Path(ledger_path).exists():
        print(f"ERROR: ledger 없음: {ledger_path}", file=sys.stderr)
        sys.exit(1)

    entries = load_jsonl(Path(ledger_path))
    clusters = aggregate_frequency(entries, days=args.days, min_count=args.threshold, include_resolved=args.include_resolved)
    recommendations = [recommend_action(c) for c in clusters]
    print(format_report(clusters, recommendations, args.days, args.threshold, as_json=args.json))


if __name__ == "__main__":
    main()
