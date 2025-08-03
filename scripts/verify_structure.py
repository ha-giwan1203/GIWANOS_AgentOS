#!/usr/bin/env python3
"""
verify_structure.py

A lightweight CLI tool that validates the VELOS (GIWANOS) repository layout
against the official folder/file specification.

Usage (from repository root):

    python verify_structure.py
    python verify_structure.py --root C:\\giwanos
    python verify_structure.py --show-extras

Return codes:
    0  – all checks passed
    1  – missing paths or type mismatches detected
"""

import os
import argparse
import sys
from typing import List, Dict, Tuple


# --------------------------------------------------------------------------- #
# Specification of expected directories and files (relative to repository root)
# --------------------------------------------------------------------------- #
EXPECTED_DIRS = [
    "scripts",
    "modules",
    "modules/core",
    "modules/advanced",
    "modules/automation",
    "modules/automation/git_management",
    "modules/automation/scheduling",
    "modules/automation/snapshots",
    "modules/evaluation",
    "modules/evaluation/xai",
    "modules/evaluation/xai/models",
    "modules/evaluation/giwanos_agent",
    "modules/evaluation/insight",
    "configs",
    "configs/security",
    "data",
    "data/logs",
    "data/reports",
    "data/reflections",
    "data/memory",
    "data/backups",
    "interface",
    "interface/user_personalization",
    "vector_cache",
    "fonts",
    "fonts/Nanum_Gothic",
]

EXPECTED_FILES = [
    # scripts
    "scripts/run_giwanos_master_loop.py",
    "scripts/setup_giwanos_tasks.ps1",
    "scripts/generate_decision_rules.py",
    "scripts/generate_rag_decision_examples.py",
    "scripts/auto_recovery_agent.py",
    "scripts/reflection_agent.py",
    # modules/core
    "modules/core/context_aware_decision_engine.py",
    "modules/core/adaptive_reasoning_agent.py",
    "modules/core/auto_recovery_agent.py",
    "modules/core/reflection_agent.py",
    "modules/core/threshold_optimizer.py",
    "modules/core/rule_optimizer.py",
    # modules/advanced
    "modules/advanced/advanced_rag.py",
    "modules/advanced/advanced_vectordb.py",
    "modules/advanced/semantic_cache.py",
    # modules/automation
    "modules/automation/smart_backup_recovery.py",
    "modules/automation/git_management/git_sync.py",
    # modules/evaluation
    "modules/evaluation/xai/models/xai_explanation_model.py",
    "modules/evaluation/giwanos_agent/judge_agent.py",
    "modules/evaluation/insight/system_insight_agent.py",
    # configs
    "configs/.env",
    "configs/fallback_stats.json",
    "configs/judgment_rules.json",
    "configs/settings.yaml",
    "configs/system_config.json",
    "configs/security/config.key",
    "configs/security/encrypt_config.py",
    # interface
    "interface/status_dashboard.py",
    "interface/user_personalization/user_personalization_model.py",
    # vector_cache
    "vector_cache/cache_responses.npy",
    "vector_cache/embeddings.npy",
    "vector_cache/local_index.faiss",
    # fonts
    "fonts/Nanum_Gothic/NanumGothic-Regular.ttf",
]

EXPECTED = {p: "dir" for p in EXPECTED_DIRS}
EXPECTED.update({p: "file" for p in EXPECTED_FILES})


# --------------------------------------------------------------------------- #
def scan_repo(root: str) -> Tuple[List[str], List[str], List[str]]:
    """Return missing, type mismatches, extras (dirs & files)."""
    missing, mismatches, extras = [], [], []

    # Normalize expected paths
    for rel_path, expected_type in EXPECTED.items():
        abs_path = os.path.join(root, rel_path)
        if not os.path.exists(abs_path):
            missing.append(rel_path)
        else:
            if expected_type == "dir" and not os.path.isdir(abs_path):
                mismatches.append(f"{rel_path} (expected dir, found file)")
            elif expected_type == "file" and not os.path.isfile(abs_path):
                mismatches.append(f"{rel_path} (expected file, found dir)")

    # Detect extras
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "." if rel_dir == "." else rel_dir.replace("\\", "/")
        # Current directory
        if rel_dir not in EXPECTED and rel_dir != ".":
            extras.append(rel_dir)
        # Sub‑dirs & files
        for d in dirnames:
            rel = os.path.join(rel_dir, d).replace("\\", "/")
            if rel not in EXPECTED:
                extras.append(rel)
        for f in filenames:
            rel = os.path.join(rel_dir, f).replace("\\", "/")
            if rel not in EXPECTED:
                extras.append(rel)

    return missing, mismatches, sorted(set(extras))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate VELOS repository structure.")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--show-extras",
        action="store_true",
        help="Show items that are present but not part of the spec",
    )
    args = parser.parse_args()
    root = os.path.abspath(args.root)

    missing, mismatches, extras = scan_repo(root)

    any_issue = False
    if missing:
        any_issue = True
        print("Missing:")
        for p in missing:
            print(f"  - {p}")
        print()

    if mismatches:
        any_issue = True
        print("Type mismatches:")
        for p in mismatches:
            print(f"  - {p}")
        print()

    if args.show_extras:
        print("Extras:")
        if extras:
            for p in extras:
                print(f"  - {p}")
        else:
            print("  (none)")
        print()

    if not any_issue:
        print("All checks passed! ✔️")

    sys.exit(1 if any_issue else 0)


if __name__ == "__main__":
    main()
