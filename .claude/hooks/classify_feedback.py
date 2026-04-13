#!/usr/bin/env python3
"""feedback_*.md에 enforcement 태그(hookable/promptable/human_only) 추가.

세션40 학습 루프 완성 — MEMORY feedback 3분류.
GPT 토론 합의 기준: "기계판정 가능성" 3문항 판정 트리.
  1) 기계가 명확한 pass/fail로 판정 가능? → No면 promptable 이상
  2) Hook/스크립트가 실행 시점에 관측 가능? → No면 promptable
  3) 자동 강제 시 오탐 비용 감당 가능? → Yes면 hookable, No면 human_only/promptable

Usage:
  python3 .claude/hooks/classify_feedback.py --dry-run   # 미리보기
  python3 .claude/hooks/classify_feedback.py             # 실제 적용
  python3 .claude/hooks/classify_feedback.py --validate  # 태그 누락 검사
  python3 .claude/hooks/classify_feedback.py --json      # JSON 출력
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# === 사전 분류 매핑 (세션40 GPT 토론 합의) ===
# 3문항 판정 트리 기반 수동 분류
CLASSIFICATION: dict[str, str] = {
    # hookable (8건): hook/gate로 자동 강제 가능
    "feedback_auto_update_on_completion": "hookable",
    "feedback_commit_before_gpt_share": "hookable",
    "feedback_debate_independent_review": "hookable",
    "feedback_folder_creation_rules": "hookable",
    "feedback_independent_gpt_review": "hookable",
    "feedback_post_completion_routine": "hookable",
    "feedback_share_all_commits": "hookable",
    "feedback_zdm_sunday_skip": "hookable",
    # human_only (3건): 인간 규율 필요, 자동화 불가
    "feedback_excel_formatting": "human_only",
    "feedback_settlement_mistakes": "human_only",
    "feedback_daily_task_mistakes": "human_only",
    # promptable (나머지 22건): CLAUDE.md/프롬프트로 유도
    "feedback_always_read_instructions": "promptable",
    "feedback_always_read_skill_first": "promptable",
    "feedback_browser_chrome_mcp_only": "promptable",
    "feedback_chatgpt_tab_reuse": "promptable",
    "feedback_debate_mode_check_before_respond": "promptable",
    "feedback_debate_mode_first_room": "promptable",
    "feedback_debate_mode_read_docs": "promptable",
    "feedback_debate_mode_workflow": "promptable",
    "feedback_follow_cowork_rules": "promptable",
    "feedback_gpt_input_inserttext": "promptable",
    "feedback_gpt_output_verification": "promptable",
    "feedback_no_approval_prompts": "promptable",
    "feedback_no_idle_report": "promptable",
    "feedback_no_pr_workflow": "promptable",
    "feedback_parallel_first": "promptable",
    "feedback_proactive_self_review": "promptable",
    "feedback_settlement_month_naming": "promptable",
    "feedback_share_not_report": "promptable",
    "feedback_system_map_first": "promptable",
    "feedback_tone_rules": "promptable",
    "feedback_use_skills_not_manual": "promptable",
    "feedback_worktree_main_direct": "promptable",
}


def find_memory_dir() -> Path:
    """프로젝트 메모리 디렉터리 자동 탐색."""
    candidates = [
        Path.home() / ".claude" / "projects" / "C--Users-User-Desktop------" / "memory",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    # fallback: glob
    base = Path.home() / ".claude" / "projects"
    if base.is_dir():
        for d in base.iterdir():
            mem = d / "memory"
            if mem.is_dir() and list(mem.glob("feedback_*.md")):
                return mem
    return candidates[0]


def read_frontmatter(filepath: Path) -> tuple[list[str], int, int]:
    """YAML frontmatter 라인과 경계 인덱스 반환."""
    lines = filepath.read_text(encoding="utf-8").split("\n")
    fm_start = fm_end = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if fm_start == -1:
                fm_start = i
            else:
                fm_end = i
                break
    return lines, fm_start, fm_end


def has_enforcement_tag(filepath: Path) -> bool:
    """이미 enforcement 태그가 있는지 확인."""
    lines, fm_start, fm_end = read_frontmatter(filepath)
    if fm_start == -1 or fm_end == -1:
        return False
    for i in range(fm_start + 1, fm_end):
        if lines[i].startswith("enforcement:"):
            return True
    return False


def add_enforcement_tag(filepath: Path, enforcement: str, dry_run: bool = False) -> bool:
    """frontmatter에 enforcement 태그 삽입. 수정되면 True."""
    lines, fm_start, fm_end = read_frontmatter(filepath)
    if fm_start == -1 or fm_end == -1:
        return False
    # 이미 있으면 skip
    for i in range(fm_start + 1, fm_end):
        if lines[i].startswith("enforcement:"):
            return False
    # type: 줄 뒤에 삽입
    inserted = False
    for i in range(fm_start + 1, fm_end):
        if lines[i].startswith("type:"):
            lines.insert(i + 1, f"enforcement: {enforcement}")
            inserted = True
            break
    if not inserted:
        # type: 줄이 없으면 frontmatter 끝 바로 앞에 삽입
        lines.insert(fm_end, f"enforcement: {enforcement}")
    if not dry_run:
        filepath.write_text("\n".join(lines), encoding="utf-8")
    return True


def classify_and_apply(memory_dir: Path, dry_run: bool = False) -> list[dict]:
    """모든 feedback_*.md 파일을 분류하고 태깅."""
    results = []
    for fp in sorted(memory_dir.glob("feedback_*.md")):
        stem = fp.stem
        enforcement = CLASSIFICATION.get(stem, "promptable")
        already = has_enforcement_tag(fp)
        modified = False
        if not already:
            modified = add_enforcement_tag(fp, enforcement, dry_run=dry_run)
        results.append({
            "file": fp.name,
            "enforcement": enforcement,
            "already_tagged": already,
            "modified": modified,
            "dry_run": dry_run,
        })
    return results


def validate(memory_dir: Path) -> list[str]:
    """enforcement 태그 누락 파일 목록 반환."""
    missing = []
    for fp in sorted(memory_dir.glob("feedback_*.md")):
        if not has_enforcement_tag(fp):
            missing.append(fp.name)
    return missing


def format_report(results: list[dict], as_json: bool = False) -> str:
    if as_json:
        return json.dumps(results, ensure_ascii=False, indent=2)

    lines = ["=== MEMORY Feedback 3분류 ===", ""]
    counts = {"hookable": 0, "promptable": 0, "human_only": 0}
    for r in results:
        counts[r["enforcement"]] = counts.get(r["enforcement"], 0) + 1
        status = "SKIP(이미)" if r["already_tagged"] else ("DRY" if r["dry_run"] else "OK")
        lines.append(f"  [{status}] {r['file']:50s} → {r['enforcement']}")
    lines.append("")
    lines.append(f"합계: hookable {counts.get('hookable',0)} / promptable {counts.get('promptable',0)} / human_only {counts.get('human_only',0)}")
    lines.append(f"전체 {len(results)}건")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MEMORY feedback 3분류 (hookable/promptable/human_only)")
    parser.add_argument("--memory-dir", type=Path, default=None, help="memory 디렉터리 경로")
    parser.add_argument("--dry-run", action="store_true", help="미리보기만 (파일 수정 안 함)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--validate", action="store_true", help="enforcement 태그 누락 검사")
    parser.add_argument("--force", action="store_true", help="기존 태그 덮어쓰기 (미구현)")
    args = parser.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    if not memory_dir.is_dir():
        print(f"ERROR: memory 디렉터리 없음: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    if args.validate:
        missing = validate(memory_dir)
        if missing:
            print(f"enforcement 태그 누락 {len(missing)}건:")
            for m in missing:
                print(f"  - {m}")
            sys.exit(1)
        else:
            print("ALL OK: 모든 feedback 파일에 enforcement 태그 있음")
            sys.exit(0)

    results = classify_and_apply(memory_dir, dry_run=args.dry_run)
    print(format_report(results, as_json=args.json))


if __name__ == "__main__":
    main()
