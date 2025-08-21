#!/usr/bin/env python3
"""
VELOS Phase 2 Analysis: Configuration Cleanup and Path Standardization
Analyzes system-wide configuration hierarchy and path references for standardization.
"""

import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


def analyze_config_files():
    """Analyze configuration file hierarchy"""
    print("=== Configuration File Analysis ===")

    # Find all config files
    config_extensions = ["*.yaml", "*.yml", "*.json", "*.cfg", "*.ini", "*.toml"]
    find_cmd = (
        ["find", ".", "-name"]
        + [f"-o -name {ext}" for ext in config_extensions[:-1]]
        + [config_extensions[-1]]
    )
    find_cmd = ["find"] + [
        item
        for sublist in [[".", "-name", ext] for ext in config_extensions]
        for item in sublist
        if item != config_extensions[0]
    ]

    # Simplified approach
    result = subprocess.run(
        [
            "find",
            ".",
            "-name",
            "*.yaml",
            "-o",
            "-name",
            "*.yml",
            "-o",
            "-name",
            "*.json",
            "-o",
            "-name",
            "*.cfg",
            "-o",
            "-name",
            "*.ini",
            "-o",
            "-name",
            "*.toml",
        ],
        cwd="/home/user/webapp",
        capture_output=True,
        text=True,
    )

    config_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

    # Categorize by directory
    by_dir = defaultdict(list)
    for f in config_files:
        if f:
            dir_name = os.path.dirname(f) or "root"
            by_dir[dir_name].append(f)

    print(f"Total configuration files: {len(config_files)}")
    print("\nConfiguration files by directory:")
    for dir_name, files in sorted(by_dir.items()):
        print(f"  {dir_name}: {len(files)} files")
        if len(files) <= 5:  # Show files for small directories
            for f in files:
                print(f"    {f}")

    return config_files, by_dir


def analyze_path_references():
    """Analyze /home/user/webapp path references"""
    print("\n=== Path Reference Analysis ===")

    # Count files with /home/user/webapp references
    result = subprocess.run(
        [
            "grep",
            "-rl",
            "/home/user/webapp",
            "--include=*.py",
            "--include=*.yaml",
            "--include=*.yml",
            "--include=*.json",
            ".",
        ],
        cwd="/home/user/webapp",
        capture_output=True,
        text=True,
    )

    files_with_paths = result.stdout.strip().split("\n") if result.stdout.strip() else []

    # Count total lines with references
    result_lines = subprocess.run(
        [
            "grep",
            "-r",
            "/home/user/webapp",
            "--include=*.py",
            "--include=*.yaml",
            "--include=*.yml",
            "--include=*.json",
            ".",
        ],
        cwd="/home/user/webapp",
        capture_output=True,
        text=True,
    )

    total_refs = len(result_lines.stdout.strip().split("\n")) if result_lines.stdout.strip() else 0

    print(f"Files with /home/user/webapp references: {len(files_with_paths)}")
    print(f"Total /home/user/webapp references: {total_refs}")

    # Categorize by file type and directory
    by_type = defaultdict(list)
    by_dir = defaultdict(list)

    for f in files_with_paths:
        if f:
            ext = os.path.splitext(f)[1] or "no_ext"
            by_type[ext].append(f)

            dir_name = os.path.dirname(f) or "root"
            by_dir[dir_name].append(f)

    print("\nFiles by type:")
    for ext, files in sorted(by_type.items()):
        print(f"  {ext}: {len(files)} files")

    print("\nFiles by directory (top 10):")
    sorted_dirs = sorted(by_dir.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for dir_name, files in sorted_dirs:
        print(f"  {dir_name}: {len(files)} files")

    return files_with_paths, by_type, by_dir


def analyze_critical_modules():
    """Analyze critical system modules that need path standardization"""
    print("\n=== Critical Module Analysis ===")

    critical_paths = [
        "configs/",
        "modules/core/",
        "modules/memory/",
        "modules/automation/",
        "scripts/",
    ]

    critical_files = []
    for path in critical_paths:
        result = subprocess.run(
            ["find", path, "-name", "*.py", "-exec", "grep", "-l", "/home/user/webapp", "{}", ";"],
            cwd="/home/user/webapp",
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            path_files = result.stdout.strip().split("\n")
            critical_files.extend(path_files)
            print(f"{path}: {len(path_files)} files need updating")

    return critical_files


def create_phase2_plan():
    """Create detailed Phase 2 execution plan"""
    print("\n=== Phase 2 Execution Plan ===")

    plan = {
        "priority_1_critical": [
            "configs/settings.yaml",
            "modules/core/db_util.py",
            "modules/core/memory_adapter/adapter.py",
            "modules/memory/storage/sqlite_store.py",
        ],
        "priority_2_core_modules": [
            "modules/core/",
            "modules/memory/",
            "modules/automation/scheduling/",
        ],
        "priority_3_scripts": ["scripts/", "configs/"],
        "priority_4_bulk_updates": ["data/", "logs/", "artifacts/"],
    }

    standardization_rules = {
        "windows_path": "/home/user/webapp",
        "linux_sandbox_path": "/home/user/webapp",
        "environment_variable": "VELOS_ROOT_PATH",
        "fallback_logic": "os.environ.get('VELOS_ROOT_PATH', '/home/user/webapp' if os.name == 'nt' else '/home/user/webapp')",
    }

    print("Priority levels:")
    for priority, items in plan.items():
        print(f"  {priority}: {len(items)} items")

    print("\nStandardization approach:")
    for rule, value in standardization_rules.items():
        print(f"  {rule}: {value}")

    return plan, standardization_rules


def main():
    """Run complete Phase 2 analysis"""
    print("VELOS Phase 2 Analysis - Configuration Cleanup and Path Standardization")
    print("=" * 80)

    # Analysis steps
    config_files, config_by_dir = analyze_config_files()
    path_files, path_by_type, path_by_dir = analyze_path_references()
    critical_files = analyze_critical_modules()
    plan, rules = create_phase2_plan()

    # Summary
    print("\n" + "=" * 80)
    print("PHASE 2 ANALYSIS SUMMARY:")
    print("=" * 80)
    print(f"Configuration files to review: {len(config_files)}")
    print(f"Files with path references: {len(path_files)}")
    print(f"Critical files needing immediate attention: {len(critical_files)}")

    print("\nNext Steps:")
    print("1. 🔧 Update critical configuration files (Priority 1)")
    print("2. 🏗️ Standardize core module paths (Priority 2)")
    print("3. 📝 Update script path references (Priority 3)")
    print("4. 🔄 Bulk update remaining files (Priority 4)")

    print("\n⚡ Ready to proceed with Phase 2 implementation!")

    return {
        "config_files": len(config_files),
        "path_files": len(path_files),
        "critical_files": len(critical_files),
        "plan": plan,
        "rules": rules,
    }


if __name__ == "__main__":
    analysis = main()
