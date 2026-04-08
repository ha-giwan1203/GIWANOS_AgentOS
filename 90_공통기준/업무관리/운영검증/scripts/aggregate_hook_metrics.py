#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook 4지표 집계 스크립트
- 승인 요청 수: hook_log에서 PreToolUse 이벤트 총 수
- deny 수: incident_ledger에서 gate_reject + hook_block 합계
- 오탐 수: incident_ledger에서 false_positive 태깅 건수 (resolved와 분리)
- 우회 감지 수: incident_ledger에서 bypass 관련 건수
"""
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))

# --- 분류 기준 ---

# hook_log event 중 "검사 발화"로 볼 이벤트 접두어
APPROVAL_EVENT_PREFIXES = ("PreToolUse",)

# incident_ledger type별 분류
DENY_TYPES = {"gate_reject", "hook_block"}
BYPASS_KEYWORDS = {"bypass", "우회", "override_without_approval"}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


KNOWN_HOOKS = {
    "block_dangerous", "commit_gate", "date_scope_guard", "evidence_gate",
    "protect_files", "send_gate", "stop_guard", "gpt_followup_post",
    "gpt_followup_stop", "completion_gate", "evidence_stop_guard",
    "auto_compile", "write_marker", "evidence_mark_read",
    "risk_profile_prompt", "notify_slack",
}


# hook 이름이 msg에 직접 포함되지 않는 경우의 패턴→hook 매핑
MSG_PATTERN_MAP = [
    ("git commit 감지", "commit_gate"),
    ("debate_quality", "send_gate"),
    ("일요일", "date_scope_guard"),
    ("요일 확인 없이", "date_scope_guard"),
    ("date_check.req", "evidence_gate"),
    ("auth_diag.req", "evidence_gate"),
    ("skill_read.req", "evidence_gate"),
    ("tasks_handoff.req", "evidence_gate"),
    ("보호 경로 삭제", "protect_files"),
    ("보호 경로", "protect_files"),
    ("command 파싱 실패", "block_dangerous"),
    ("python 경유 보호 파일", "block_dangerous"),
]


def extract_hook_name(msg: str) -> str:
    """hook_log msg에서 hook 이름 추출. 알려진 hook 이름 우선 매칭, 패턴 폴백."""
    if not msg:
        return "unknown"
    msg_lower = msg.lower()
    for hook in KNOWN_HOOKS:
        if hook in msg_lower:
            return hook
    # 패턴 폴백: msg에 hook 이름이 없지만 내용으로 추론 가능한 경우
    for pattern, hook in MSG_PATTERN_MAP:
        if pattern.lower() in msg_lower:
            return hook
    return "unknown"


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def aggregate(hook_log_path: Path, incident_log_path: Path) -> dict:
    hook_rows = load_jsonl(hook_log_path)
    incident_rows = load_jsonl(incident_log_path)

    totals = Counter()
    by_hook = defaultdict(Counter)

    # 1) hook_log → 승인 요청(검사 발화) 수
    for row in hook_rows:
        event = row.get("event", "")
        if any(event.startswith(p) for p in APPROVAL_EVENT_PREFIXES):
            hook_name = extract_hook_name(row.get("msg", ""))
            totals["approval_requests"] += 1
            by_hook[hook_name]["approval_requests"] += 1

    # 2) incident_ledger → deny / 오탐 / 우회
    for row in incident_rows:
        inc_type = row.get("type", "")
        hook_name = row.get("hook", "unknown")
        detail = row.get("detail", "").lower()
        resolved = row.get("resolved", False)

        # deny
        if inc_type in DENY_TYPES:
            totals["deny_count"] += 1
            by_hook[hook_name]["deny_count"] += 1

        # 오탐 (false_positive 전용 필드 — resolved와 분리)
        fp_flag = row.get("false_positive", False)
        classification = str(row.get("classification", "")).lower()
        if fp_flag is True or classification in {"false_positive", "fp", "오탐"}:
            totals["false_positive_count"] += 1
            by_hook[hook_name]["false_positive_count"] += 1

        # 우회 감지
        if any(kw in detail for kw in BYPASS_KEYWORDS):
            totals["bypass_detected_count"] += 1
            by_hook[hook_name]["bypass_detected_count"] += 1

    report = {
        "generated_at": datetime.now(KST).isoformat(timespec="seconds"),
        "source": {
            "hook_log": str(hook_log_path),
            "incident_log": str(incident_log_path),
        },
        "log_stats": {
            "hook_log_lines": len(hook_rows),
            "incident_log_lines": len(incident_rows),
        },
        "totals": {
            "approval_requests": totals["approval_requests"],
            "deny_count": totals["deny_count"],
            "false_positive_count": totals["false_positive_count"],
            "bypass_detected_count": totals["bypass_detected_count"],
        },
        "rates": {
            "deny_rate_raw": safe_rate(totals["deny_count"], totals["approval_requests"]),
            "deny_rate_effective": safe_rate(
                totals["deny_count"] - totals["false_positive_count"],
                totals["approval_requests"],
            ),
            "false_positive_rate": safe_rate(
                totals["false_positive_count"], totals["deny_count"]
            ),
            "bypass_rate": safe_rate(
                totals["bypass_detected_count"], totals["approval_requests"]
            ),
        },
        "by_hook": {
            hook: {
                "approval_requests": data["approval_requests"],
                "deny_count": data["deny_count"],
                "false_positive_count": data["false_positive_count"],
                "bypass_detected_count": data["bypass_detected_count"],
            }
            for hook, data in sorted(by_hook.items())
        },
    }
    return report


def render_markdown(report: dict) -> str:
    t = report["totals"]
    r = report["rates"]
    s = report["log_stats"]
    lines = [
        "# Hook 4지표 집계",
        "",
        f"- 생성시각: {report['generated_at']}",
        f"- hook_log: {s['hook_log_lines']}건 / incident_ledger: {s['incident_log_lines']}건",
        "",
        "## 합계",
        "",
        f"| 지표 | 건수 | 비율 |",
        f"|------|------|------|",
        f"| 승인 요청 (hook 발화) | {t['approval_requests']} | - |",
        f"| deny (raw) | {t['deny_count']} | {r['deny_rate_raw']:.2%} |",
        f"| deny (effective, 오탐 제외) | {t['deny_count'] - t['false_positive_count']} | {r['deny_rate_effective']:.2%} |",
        f"| 오탐 (false_positive) | {t['false_positive_count']} | {r['false_positive_rate']:.2%} |",
        f"| 우회 감지 | {t['bypass_detected_count']} | {r['bypass_rate']:.2%} |",
        "",
        "## hook별 상세",
        "",
        "| hook | 발화 | deny | 오탐 | 우회 |",
        "|------|------|------|------|------|",
    ]
    for hook, data in sorted(
        report["by_hook"].items(),
        key=lambda x: x[1]["deny_count"],
        reverse=True,
    ):
        lines.append(
            f"| {hook} | {data['approval_requests']} | {data['deny_count']} "
            f"| {data['false_positive_count']} | {data['bypass_detected_count']} |"
        )
    lines.append("")
    lines.append("## 판정 기준")
    lines.append("")
    lines.append("- deny_rate_raw = deny 전체 / 승인요청 (가드레일 강도)")
    lines.append("- deny_rate_effective = (deny - 오탐) / 승인요청 (실제 위반 비율)")
    lines.append("- false_positive_rate = 오탐 / deny (높으면 잘못 막는 비율 높음)")
    lines.append("- bypass_rate = 우회 / 승인요청 (0이어야 정상)")
    lines.append("- 오탐 태깅: incident_ledger에서 false_positive=true 또는 classification=fp/오탐으로 표기")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Hook 4지표 집계")
    parser.add_argument(
        "--hook-log",
        default=".claude/hooks/hook_log.jsonl",
        help="hook_log.jsonl 경로",
    )
    parser.add_argument(
        "--incident-log",
        default=".claude/incident_ledger.jsonl",
        help="incident_ledger.jsonl 경로",
    )
    parser.add_argument(
        "--out-json",
        default="90_공통기준/업무관리/운영검증/reports/hook_metrics_latest.json",
    )
    parser.add_argument(
        "--out-md",
        default="90_공통기준/업무관리/운영검증/reports/hook_metrics_latest.md",
    )
    args = parser.parse_args()

    hook_log_path = Path(args.hook_log)
    incident_log_path = Path(args.incident_log)
    out_json_path = Path(args.out_json)
    out_md_path = Path(args.out_md)

    report = aggregate(hook_log_path, incident_log_path)

    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)

    out_json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    out_md_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"JSON → {out_json_path}")
    print(f"MD   → {out_md_path}")
    print(f"승인요청: {report['totals']['approval_requests']} / "
          f"deny: {report['totals']['deny_count']} / "
          f"오탐: {report['totals']['false_positive_count']} / "
          f"우회: {report['totals']['bypass_detected_count']}")


if __name__ == "__main__":
    main()
