#!/usr/bin/env python3
"""
VELOS System Completeness Analysis
Identifies remaining areas for improvement after Phase 1-3 completion.
"""

import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


class SystemCompletenessAnalyzer:
    """Analyzes system completeness and identifies improvement areas"""

    def __init__(self):
        self.base_path = Path("/home/user/webapp")
        self.issues = defaultdict(list)
        self.recommendations = defaultdict(list)

    def analyze_remaining_path_references(self):
        """Analyze remaining /home/user/webapp path references"""
        print("=== Remaining Path Reference Analysis ===")

        try:
            result = subprocess.run(
                ["grep", "-r", "/home/user/webapp", "--include=*.py", "--include=*.json", "."],
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
            )

            if result.stdout:
                lines = result.stdout.strip().split("\n")

                # Categorize remaining references
                categories = {
                    "data_files": [],
                    "config_files": [],
                    "log_files": [],
                    "script_files": [],
                    "other": [],
                }

                for line in lines:
                    if ":" in line:
                        file_path = line.split(":", 1)[0]

                        if "data/" in file_path:
                            categories["data_files"].append(line)
                        elif "config" in file_path:
                            categories["config_files"].append(line)
                        elif "log" in file_path:
                            categories["log_files"].append(line)
                        elif "script" in file_path:
                            categories["script_files"].append(line)
                        else:
                            categories["other"].append(line)

                print(f"Total remaining /home/user/webapp references: {len(lines)}")
                for category, items in categories.items():
                    if items:
                        print(f"  {category}: {len(items)} references")
                        if category == "data_files" and len(items) > 500:
                            self.issues["bulk_data_update"].append(
                                f"Large number of data files need path updates: {len(items)}"
                            )

                return categories
            else:
                print("✅ No remaining /home/user/webapp references found")
                return {}

        except Exception as e:
            self.issues["analysis_error"].append(f"Path reference analysis failed: {e}")
            return {}

    def analyze_import_health(self):
        """Analyze import system health and remaining issues"""
        print("\n=== Import System Health Analysis ===")

        # Check for remaining sys.path manipulations
        try:
            result = subprocess.run(
                ["grep", "-c", "sys.path", "--include=*.py", "-r", "."],
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
            )

            if result.stdout:
                lines = result.stdout.strip().split("\n")
                files_with_syspath = []

                for line in lines:
                    if ":" in line:
                        file_path, count = line.split(":", 1)
                        if int(count) > 0 and not any(
                            skip in file_path
                            for skip in ["import_manager.py", "phase3_", "__pycache__", ".git"]
                        ):
                            files_with_syspath.append((file_path, int(count)))

                files_with_syspath.sort(key=lambda x: x[1], reverse=True)

                print(f"Files still using sys.path: {len(files_with_syspath)}")

                if len(files_with_syspath) > 20:
                    self.issues["import_optimization"].append(
                        f"Still {len(files_with_syspath)} files with sys.path usage"
                    )
                    print("  Top files needing optimization:")
                    for file_path, count in files_with_syspath[:5]:
                        print(f"    {file_path}: {count} occurrences")

                return files_with_syspath

        except Exception as e:
            self.issues["import_analysis"].append(f"Import analysis failed: {e}")
            return []

    def analyze_code_quality_issues(self):
        """Analyze code quality and potential issues"""
        print("\n=== Code Quality Analysis ===")

        quality_issues = {
            "todo_comments": 0,
            "fixme_comments": 0,
            "hardcoded_paths": 0,
            "deprecated_patterns": 0,
        }

        try:
            # Check for TODO/FIXME comments
            for pattern in ["TODO", "FIXME", "XXX", "HACK"]:
                result = subprocess.run(
                    ["grep", "-r", pattern, "--include=*.py", "."],
                    cwd=str(self.base_path),
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    count = len(result.stdout.strip().split("\n"))
                    quality_issues[f"{pattern.lower()}_comments"] = count

            # Check for hardcoded paths that aren't using path manager
            result = subprocess.run(
                ["grep", "-r", "os.path.join.*data", "--include=*.py", "."],
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
            )
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                # Filter out files that already use path manager
                hardcoded = [line for line in lines if "path_manager" not in line.lower()]
                quality_issues["hardcoded_paths"] = len(hardcoded)

            print("Code quality metrics:")
            for metric, count in quality_issues.items():
                if count > 0:
                    print(f"  {metric}: {count}")
                    if count > 10:
                        self.issues["code_quality"].append(f"High number of {metric}: {count}")

            return quality_issues

        except Exception as e:
            self.issues["quality_analysis"].append(f"Quality analysis failed: {e}")
            return quality_issues

    def analyze_test_coverage(self):
        """Analyze test coverage and testing infrastructure"""
        print("\n=== Test Coverage Analysis ===")

        test_info = {"test_files": 0, "test_directories": [], "untested_modules": []}

        # Find test files
        test_patterns = ["test_*.py", "*_test.py", "tests.py"]
        for pattern in test_patterns:
            result = subprocess.run(
                ["find", ".", "-name", pattern, "-type", "f"],
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
            )
            if result.stdout:
                test_files = result.stdout.strip().split("\n")
                test_info["test_files"] += len([f for f in test_files if f])

        # Find test directories
        for item in self.base_path.iterdir():
            if item.is_dir() and "test" in item.name.lower():
                test_info["test_directories"].append(str(item))

        # Check critical modules without tests
        critical_modules = [
            "modules/core/path_manager.py",
            "modules/core/import_manager.py",
            "modules/core/db_util.py",
            "modules/memory/storage/sqlite_store.py",
        ]

        for module in critical_modules:
            module_path = self.base_path / module
            if module_path.exists():
                # Look for corresponding test file
                test_variants = [
                    module.replace(".py", "_test.py"),
                    module.replace(".py", "").replace("/", "/test_") + ".py",
                    f"tests/{module.replace('modules/', '').replace('.py', '_test.py')}",
                ]

                has_test = any((self.base_path / variant).exists() for variant in test_variants)
                if not has_test:
                    test_info["untested_modules"].append(module)

        print(f"Test files found: {test_info['test_files']}")
        print(f"Test directories: {len(test_info['test_directories'])}")
        print(f"Untested critical modules: {len(test_info['untested_modules'])}")

        if test_info["untested_modules"]:
            self.issues["testing"].extend(
                [f"No tests for: {module}" for module in test_info["untested_modules"]]
            )
            print("  Critical modules without tests:")
            for module in test_info["untested_modules"]:
                print(f"    {module}")

        return test_info

    def analyze_documentation_gaps(self):
        """Analyze documentation completeness"""
        print("\n=== Documentation Analysis ===")

        doc_info = {"readme_files": 0, "doc_directories": [], "undocumented_modules": []}

        # Find README files
        for readme_name in ["README.md", "README.rst", "README.txt"]:
            if (self.base_path / readme_name).exists():
                doc_info["readme_files"] += 1

        # Find documentation directories
        for item in self.base_path.iterdir():
            if item.is_dir() and item.name.lower() in ["docs", "doc", "documentation"]:
                doc_info["doc_directories"].append(str(item))

        # Check for module documentation
        for module_dir in ["modules/core", "modules/memory", "modules/automation"]:
            module_path = self.base_path / module_dir
            if module_path.exists():
                py_files = list(module_path.glob("**/*.py"))
                documented_files = []

                for py_file in py_files:
                    if py_file.name != "__init__.py":
                        try:
                            with open(py_file, "r", encoding="utf-8") as f:
                                content = f.read()
                                if '"""' in content or "'''" in content:
                                    documented_files.append(py_file)
                        except Exception:
                            pass

                undoc_ratio = 1 - (len(documented_files) / max(len(py_files), 1))
                if undoc_ratio > 0.5:  # More than 50% undocumented
                    doc_info["undocumented_modules"].append(module_dir)

        print(f"README files: {doc_info['readme_files']}")
        print(f"Documentation directories: {len(doc_info['doc_directories'])}")
        print(f"Modules needing better documentation: {len(doc_info['undocumented_modules'])}")

        if doc_info["readme_files"] == 0:
            self.issues["documentation"].append("No main README file found")

        if not doc_info["doc_directories"]:
            self.issues["documentation"].append("No dedicated documentation directory")

        return doc_info

    def analyze_performance_opportunities(self):
        """Analyze potential performance improvements"""
        print("\n=== Performance Analysis ===")

        perf_issues = {"large_files": [], "inefficient_patterns": [], "resource_usage": {}}

        # Find large Python files (potential for refactoring)
        for py_file in self.base_path.glob("**/*.py"):
            try:
                size = py_file.stat().st_size
                if size > 50000:  # Files larger than 50KB
                    perf_issues["large_files"].append((str(py_file), size))
            except Exception:
                pass

        # Check for inefficient patterns
        inefficient_patterns = [
            ("import.*\\*", "Wildcard imports"),
            ("for.*in.*range\\(len\\(", "Inefficient iteration"),
            ("open\\([^)]+\\)(?!.*with)", "File not using context manager"),
        ]

        for pattern, description in inefficient_patterns:
            try:
                result = subprocess.run(
                    ["grep", "-r", "-P", pattern, "--include=*.py", "."],
                    cwd=str(self.base_path),
                    capture_output=True,
                    text=True,
                )
                if result.stdout:
                    count = len(result.stdout.strip().split("\n"))
                    perf_issues["inefficient_patterns"].append((description, count))
            except Exception:
                pass

        print("Performance opportunities:")
        if perf_issues["large_files"]:
            print(f"  Large files (>50KB): {len(perf_issues['large_files'])}")
            if len(perf_issues["large_files"]) > 5:
                self.issues["performance"].append(
                    f"Multiple large files may need refactoring: {len(perf_issues['large_files'])}"
                )

        for description, count in perf_issues["inefficient_patterns"]:
            if count > 0:
                print(f"  {description}: {count} occurrences")
                if count > 20:
                    self.issues["performance"].append(f"{description}: {count} occurrences")

        return perf_issues

    def generate_recommendations(self):
        """Generate specific recommendations based on analysis"""
        print("\n=== Generating Recommendations ===")

        # Phase 4 recommendations based on findings
        if self.issues.get("bulk_data_update"):
            self.recommendations["phase4_data"].append(
                "Phase 4A: Bulk Data File Path Updates - Update remaining data files with path references"
            )

        if self.issues.get("import_optimization"):
            self.recommendations["phase4_imports"].append(
                "Phase 4B: Complete Import Optimization - Finish migrating remaining files to import manager"
            )

        if self.issues.get("testing"):
            self.recommendations["testing"].append(
                "Critical: Add comprehensive test suite for core modules"
            )

        if self.issues.get("documentation"):
            self.recommendations["documentation"].append(
                "Important: Create comprehensive system documentation"
            )

        if self.issues.get("performance"):
            self.recommendations["performance"].append(
                "Enhancement: Address performance optimization opportunities"
            )

        # Security and maintenance recommendations
        self.recommendations["security"].append(
            "Security: Implement input validation and sanitization across modules"
        )

        self.recommendations["maintenance"].append(
            "Maintenance: Set up automated code quality checks (linting, formatting)"
        )

        return self.recommendations

    def create_improvement_roadmap(self):
        """Create a prioritized improvement roadmap"""
        print("\n=== Improvement Roadmap ===")

        roadmap = {
            "immediate_priority": {
                "description": "Critical issues requiring immediate attention",
                "items": [],
            },
            "short_term": {
                "description": "Important improvements for next phase (1-2 weeks)",
                "items": [],
            },
            "medium_term": {"description": "Quality improvements (1-2 months)", "items": []},
            "long_term": {"description": "Enhancement and optimization (3+ months)", "items": []},
        }

        # Categorize recommendations by priority
        critical_keywords = ["security", "critical", "core modules"]
        important_keywords = ["import", "path", "bulk"]
        quality_keywords = ["documentation", "testing"]
        enhancement_keywords = ["performance", "optimization"]

        for category, recommendations in self.recommendations.items():
            for rec in recommendations:
                if any(kw in rec.lower() for kw in critical_keywords):
                    roadmap["immediate_priority"]["items"].append(rec)
                elif any(kw in rec.lower() for kw in important_keywords):
                    roadmap["short_term"]["items"].append(rec)
                elif any(kw in rec.lower() for kw in quality_keywords):
                    roadmap["medium_term"]["items"].append(rec)
                else:
                    roadmap["long_term"]["items"].append(rec)

        return roadmap


def main():
    """Run complete system completeness analysis"""
    print("VELOS System Completeness Analysis")
    print("=" * 50)
    print("Analyzing system after Phase 1-3 completion...")

    analyzer = SystemCompletenessAnalyzer()

    # Run all analyses
    path_refs = analyzer.analyze_remaining_path_references()
    import_health = analyzer.analyze_import_health()
    code_quality = analyzer.analyze_code_quality_issues()
    test_coverage = analyzer.analyze_test_coverage()
    documentation = analyzer.analyze_documentation_gaps()
    performance = analyzer.analyze_performance_opportunities()

    # Generate recommendations
    recommendations = analyzer.generate_recommendations()
    roadmap = analyzer.create_improvement_roadmap()

    # Summary report
    print("\n" + "=" * 50)
    print("COMPLETENESS ANALYSIS SUMMARY:")
    print("=" * 50)

    total_issues = sum(len(issues) for issues in analyzer.issues.values())
    print(f"Total issues identified: {total_issues}")

    if total_issues == 0:
        print("🎉 System appears to be in excellent condition!")
    else:
        print("\nIssue categories:")
        for category, issues in analyzer.issues.items():
            if issues:
                print(f"  {category}: {len(issues)} issues")

    print(f"\nRecommendations generated: {sum(len(recs) for recs in recommendations.values())}")

    print("\n" + "=" * 50)
    print("RECOMMENDED NEXT STEPS:")
    print("=" * 50)

    for priority, info in roadmap.items():
        if info["items"]:
            print(f"\n{priority.upper().replace('_', ' ')}:")
            print(f"  {info['description']}")
            for item in info["items"][:3]:  # Show top 3 items
                print(f"  • {item}")
            if len(info["items"]) > 3:
                print(f"  ... and {len(info['items']) - 3} more items")

    return {"total_issues": total_issues, "recommendations": recommendations, "roadmap": roadmap}


if __name__ == "__main__":
    results = main()
