#!/usr/bin/env python3
"""
VELOS Phase 3 Batch Import Update: Systematic sys.path optimization
Replaces sys.path manipulations with import manager usage.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set


class ImportOptimizer:
    """Batch optimizer for import statements and sys.path usage"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.updated_files = []
        self.errors = []

    def find_sys_path_files(self) -> List[str]:
        """Find files with sys.path manipulations"""
        try:
            result = subprocess.run(
                ["grep", "-rl", "sys.path", "--include=*.py", "."],
                cwd="/home/user/webapp",
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                return result.stdout.strip().split("\n")
        except Exception as e:
            self.errors.append(f"Error finding sys.path files: {e}")
        return []

    def analyze_sys_path_patterns(self, file_path: str) -> Dict[str, List[str]]:
        """Analyze sys.path patterns in a file"""
        patterns = {"parent_manipulation": [], "direct_append": [], "path_insert": [], "other": []}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                if "sys.path" in line:
                    if ".parent" in line or "parent" in line:
                        patterns["parent_manipulation"].append((i, line.strip()))
                    elif "sys.path.append" in line:
                        patterns["direct_append"].append((i, line.strip()))
                    elif "sys.path.insert" in line:
                        patterns["path_insert"].append((i, line.strip()))
                    else:
                        patterns["other"].append((i, line.strip()))

        except Exception as e:
            self.errors.append(f"Error analyzing {file_path}: {e}")

        return patterns

    def optimize_file_imports(self, file_path: str) -> bool:
        """Optimize imports in a single file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Pattern 1: Parent path manipulations
            parent_patterns = [
                # Common pattern: Path(__file__).parent.parent
                (
                    r"sys\.path\.(?:append|insert)\([^)]*Path\(__file__\)\.parent\.parent[^)]*\)",
                    "# Replaced with import manager - Phase 3 optimization",
                ),
                # Another common pattern: os.path.dirname patterns
                (
                    r"sys\.path\.(?:append|insert)\([^)]*os\.path\.dirname\([^)]*__file__[^)]*\)[^)]*\)",
                    "# Replaced with import manager - Phase 3 optimization",
                ),
                # Direct root_dir/current_dir patterns
                (
                    r"sys\.path\.(?:append|insert)\([^)]*(?:root_dir|current_dir)[^)]*\)",
                    "# Replaced with import manager - Phase 3 optimization",
                ),
            ]

            changes_made = False
            for pattern, replacement in parent_patterns:
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                if new_content != content:
                    content = new_content
                    changes_made = True

            # Add import manager import if changes were made
            if changes_made and "from modules.core.import_manager import" not in content:
                # Find a good place to add the import
                lines = content.split("\n")

                # Find import section
                import_insert_index = -1
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        import_insert_index = i
                    elif (
                        import_insert_index != -1
                        and not line.strip().startswith(("#", "import", "from"))
                        and line.strip()
                    ):
                        break

                if import_insert_index != -1:
                    import_manager_code = """
# Phase 3: Import manager integration for optimized imports
try:
    from modules.core.import_manager import import_velos, ensure_velos_imports, add_velos_path
    _IMPORT_MANAGER_AVAILABLE = True
except ImportError:
    _IMPORT_MANAGER_AVAILABLE = False
    # Fallback for backward compatibility
    def import_velos(module_name):
        raise ImportError(f"Import manager not available for {module_name}")
"""
                    lines.insert(import_insert_index + 1, import_manager_code)
                    content = "\n".join(lines)

            # Write back if changed
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                self.updated_files.append(file_path)
                return True

            return False

        except Exception as e:
            self.errors.append(f"Error optimizing {file_path}: {e}")
            return False

    def create_import_replacements(self, file_path: str) -> Dict[str, str]:
        """Create specific import replacements for a file"""
        replacements = {}

        # Analyze what modules are being imported
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Common VELOS import patterns
            velos_imports = [
                "modules.core.db_util",
                "modules.core.path_manager",
                "modules.memory.storage.sqlite_store",
                "modules.core.memory_adapter",
                "configs.settings",
            ]

            for module in velos_imports:
                if module in content:
                    simple_name = module.split(".")[-1]
                    replacements[f"from {module} import"] = (
                        f"# Use: {simple_name} = import_velos('{module.replace('modules.', '')}')"
                    )

        except Exception:
            pass

        return replacements

    def optimize_directory(self, directory: str) -> Dict[str, int]:
        """Optimize all files in a directory"""
        print(f"\n🔧 Optimizing imports in {directory}...")

        files = []
        try:
            result = subprocess.run(
                ["find", directory, "-name", "*.py", "-exec", "grep", "-l", "sys.path", "{}", ";"],
                cwd="/home/user/webapp",
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                files = result.stdout.strip().split("\n")
        except Exception as e:
            self.errors.append(f"Error finding files in {directory}: {e}")

        stats = {"total": len(files), "optimized": 0}

        for file_path in files:
            if self.optimize_file_imports(file_path):
                stats["optimized"] += 1
                print(f"  ✅ Optimized: {file_path}")

        return stats

    def run_phase3_optimization(self) -> Dict[str, any]:
        """Run complete Phase 3 import optimization"""
        print("VELOS Phase 3 Batch Import Optimization")
        print("=" * 50)

        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")

        # Priority directories
        priority_dirs = [
            "scripts",
            "modules/memory/router",
            "modules/core",
            "interface",
            "tools",
        ]

        total_stats = {"directories": 0, "total_files": 0, "optimized_files": 0}

        for directory in priority_dirs:
            if os.path.exists(directory):
                stats = self.optimize_directory(directory)
                total_stats["directories"] += 1
                total_stats["total_files"] += stats["total"]
                total_stats["optimized_files"] += stats["optimized"]

        # Report results
        print("\n" + "=" * 50)
        print("PHASE 3 OPTIMIZATION RESULTS:")
        print("=" * 50)
        print(f"Directories processed: {total_stats['directories']}")
        print(f"Files with sys.path: {total_stats['total_files']}")
        print(f"Files optimized: {total_stats['optimized_files']}")

        if self.errors:
            print(f"\n⚠️ Errors: {len(self.errors)}")
            for error in self.errors[:3]:
                print(f"  {error}")

        return total_stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="VELOS Phase 3 Import Optimization")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying files"
    )

    args = parser.parse_args()

    optimizer = ImportOptimizer(dry_run=args.dry_run)
    results = optimizer.run_phase3_optimization()

    return optimizer


if __name__ == "__main__":
    optimizer = main()
