#!/usr/bin/env python3
"""
VELOS Phase 3 Analysis: Module Import Optimization
Analyzes sys.path manipulations and import patterns for optimization.
"""

import ast
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ImportAnalyzer:
    """Analyzer for module import patterns and sys.path usage"""

    def __init__(self):
        self.sys_path_files = []
        self.import_patterns = defaultdict(list)
        self.module_dependencies = defaultdict(set)
        self.circular_imports = []

    def find_sys_path_manipulations(self) -> Dict[str, List[str]]:
        """Find files with sys.path manipulations"""
        print("=== Sys.path Manipulation Analysis ===")

        # Find files containing sys.path
        result = subprocess.run(
            ["grep", "-r", "sys.path", "--include=*.py", "."],
            cwd="/home/user/webapp",
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            return {}

        lines = result.stdout.strip().split("\n")
        by_file = defaultdict(list)

        for line in lines:
            if ":" in line:
                file_path, content = line.split(":", 1)
                by_file[file_path].append(content.strip())

        # Categorize sys.path manipulations
        categories = {"append": [], "insert": [], "extend": [], "other": []}

        for file_path, sys_path_lines in by_file.items():
            for line in sys_path_lines:
                if "sys.path.append" in line:
                    categories["append"].append((file_path, line))
                elif "sys.path.insert" in line:
                    categories["insert"].append((file_path, line))
                elif "sys.path.extend" in line:
                    categories["extend"].append((file_path, line))
                else:
                    categories["other"].append((file_path, line))

        print(f"Files with sys.path manipulations: {len(by_file)}")
        for category, items in categories.items():
            print(f"  {category}: {len(items)} occurrences")

        return dict(by_file), categories

    def analyze_import_patterns(self) -> Dict[str, any]:
        """Analyze import patterns across the codebase"""
        print("\n=== Import Pattern Analysis ===")

        patterns = {
            "relative_imports": [],
            "absolute_imports": [],
            "dynamic_imports": [],
            "conditional_imports": [],
        }

        # Find Python files
        python_files = []
        for root, dirs, files in os.walk("/home/user/webapp"):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        print(f"Analyzing {len(python_files)} Python files...")

        import_stats = Counter()
        for py_file in python_files[:50]:  # Analyze first 50 files for speed
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST to find imports
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                import_stats[alias.name] += 1
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                import_stats[node.module] += 1
                                if node.level > 0:  # Relative import
                                    patterns["relative_imports"].append((py_file, node.module))
                                else:
                                    patterns["absolute_imports"].append((py_file, node.module))
                except SyntaxError:
                    pass

            except Exception as e:
                continue

        print(f"Top imported modules:")
        for module, count in import_stats.most_common(10):
            print(f"  {module}: {count} times")

        return patterns, import_stats

    def find_problematic_imports(self) -> List[Dict]:
        """Find imports that could be problematic"""
        print("\n=== Problematic Import Detection ===")

        problems = []

        # Find files that manipulate sys.path for local imports
        result = subprocess.run(
            ["grep", "-rn", "sys.path.*parent", "--include=*.py", "."],
            cwd="/home/user/webapp",
            capture_output=True,
            text=True,
        )

        if result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            for line in lines:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path, line_num, content = parts
                    problems.append(
                        {
                            "type": "parent_path_manipulation",
                            "file": file_path,
                            "line": line_num,
                            "content": content.strip(),
                        }
                    )

        # Find files with complex path manipulations
        result = subprocess.run(
            ["grep", "-rn", "Path(__file__).parent", "--include=*.py", "."],
            cwd="/home/user/webapp",
            capture_output=True,
            text=True,
        )

        if result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            for line in lines:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path, line_num, content = parts
                    if "sys.path" in content:
                        problems.append(
                            {
                                "type": "complex_path_manipulation",
                                "file": file_path,
                                "line": line_num,
                                "content": content.strip(),
                            }
                        )

        print(f"Found {len(problems)} problematic import patterns")
        return problems

    def suggest_optimizations(self, sys_path_data: Dict, problems: List[Dict]) -> Dict[str, List]:
        """Suggest import optimizations"""
        print("\n=== Optimization Suggestions ===")

        suggestions = {
            "centralize_imports": [],
            "use_relative_imports": [],
            "create_package_init": [],
            "remove_sys_path": [],
        }

        # Analyze sys.path manipulations
        common_patterns = defaultdict(list)
        for file_path, manipulations in sys_path_data.items():
            for manipulation in manipulations:
                if "parent" in manipulation:
                    # Extract the pattern
                    if "parent.parent" in manipulation:
                        common_patterns["double_parent"].append(file_path)
                    elif ".parent" in manipulation:
                        common_patterns["single_parent"].append(file_path)

        # Suggest centralized import management
        if len(sys_path_data) > 10:
            suggestions["centralize_imports"].append(
                "Create centralized import manager to replace scattered sys.path manipulations"
            )

        # Suggest __init__.py files
        directories_needing_init = set()
        for file_path in sys_path_data.keys():
            dir_path = os.path.dirname(file_path)
            init_path = os.path.join(dir_path, "__init__.py")
            if not os.path.exists(init_path):
                directories_needing_init.add(dir_path)

        for directory in directories_needing_init:
            suggestions["create_package_init"].append(f"Create {directory}/__init__.py")

        # Files that can remove sys.path manipulation
        for problem in problems:
            if problem["type"] in ["parent_path_manipulation", "complex_path_manipulation"]:
                suggestions["remove_sys_path"].append(problem["file"])

        # Print suggestions summary
        for category, items in suggestions.items():
            if items:
                print(f"{category}: {len(items)} items")

        return suggestions

    def create_optimization_plan(self) -> Dict[str, any]:
        """Create comprehensive optimization plan"""
        print("\n=== Creating Optimization Plan ===")

        plan = {
            "phase_3a_immediate": {
                "description": "Create centralized import manager and update core modules",
                "tasks": [
                    "Create modules/core/import_manager.py",
                    "Update 5 most critical files with sys.path issues",
                    "Create missing __init__.py files in key directories",
                ],
            },
            "phase_3b_systematic": {
                "description": "Systematic replacement of sys.path manipulations",
                "tasks": [
                    "Replace parent.parent patterns with import manager",
                    "Convert absolute paths to relative imports where possible",
                    "Update script files to use standard import patterns",
                ],
            },
            "phase_3c_validation": {
                "description": "Validate and test optimized imports",
                "tasks": [
                    "Run comprehensive import validation",
                    "Test all critical system functions",
                    "Performance benchmark comparison",
                ],
            },
        }

        return plan


def main():
    """Run complete Phase 3 import analysis"""
    print("VELOS Phase 3 Analysis - Module Import Optimization")
    print("=" * 60)

    analyzer = ImportAnalyzer()

    # Step 1: Analyze sys.path manipulations
    sys_path_data, categories = analyzer.find_sys_path_manipulations()

    # Step 2: Analyze import patterns
    patterns, import_stats = analyzer.analyze_import_patterns()

    # Step 3: Find problematic imports
    problems = analyzer.find_problematic_imports()

    # Step 4: Generate suggestions
    suggestions = analyzer.suggest_optimizations(sys_path_data, problems)

    # Step 5: Create optimization plan
    plan = analyzer.create_optimization_plan()

    # Summary report
    print("\n" + "=" * 60)
    print("PHASE 3 ANALYSIS SUMMARY:")
    print("=" * 60)
    print(f"Files with sys.path manipulations: {len(sys_path_data)}")
    print(f"Problematic import patterns: {len(problems)}")
    print(f"Optimization categories: {len(suggestions)}")

    print("\nImmediate Actions:")
    print("1. 🏗️ Create centralized import manager")
    print("2. 📁 Add missing __init__.py files")
    print("3. 🔧 Update 5 most critical files")
    print("4. ✅ Validate system functionality")

    print("\n⚡ Ready to proceed with Phase 3 implementation!")

    return {
        "sys_path_files": len(sys_path_data),
        "problems": len(problems),
        "plan": plan,
        "categories": categories,
    }


if __name__ == "__main__":
    analysis = main()
