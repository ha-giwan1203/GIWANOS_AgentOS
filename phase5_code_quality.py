#!/usr/bin/env python3
"""
VELOS Phase 5: Code Quality Improvements
Set up linting, formatting, and fix remaining code quality issues
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple


class CodeQualityImprover:
    """Handles code quality improvements including linting and formatting"""

    def __init__(self):
        self.stats = {
            "python_files_processed": 0,
            "linting_issues_found": 0,
            "formatting_issues_fixed": 0,
            "hardcoded_paths_found": 0,
            "hardcoded_paths_fixed": 0,
        }
        self.issues = []

    def setup_code_quality_tools(self) -> bool:
        """Install and configure code quality tools"""
        print("=== Setting up code quality tools ===")

        try:
            # Check if tools are already installed
            tools_to_install = []

            for tool in ["flake8", "black", "isort"]:
                try:
                    subprocess.run([tool, "--version"], capture_output=True, check=True)
                    print(f"  ✅ {tool} is already installed")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    tools_to_install.append(tool)

            if tools_to_install:
                print(f"  📦 Installing: {', '.join(tools_to_install)}")
                subprocess.run(["pip", "install"] + tools_to_install, check=True)

            # Create configuration files
            self.create_quality_configs()
            return True

        except Exception as e:
            print(f"  ❌ Error setting up tools: {e}")
            return False

    def create_quality_configs(self):
        """Create configuration files for code quality tools"""

        # .flake8 configuration
        flake8_config = """[flake8]
max-line-length = 100
exclude = 
    __pycache__,
    .git,
    .venv,
    venv,
    backups,
    data/snapshots,
    *.egg-info
ignore = 
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
    E501   # line too long (handled by black)
per-file-ignores =
    __init__.py:F401
"""

        # pyproject.toml for black and isort
        pyproject_config = """[tool.black]
line-length = 100
target-version = ['py38']
include = '\\.pyi?$'
extend-exclude = '''
/(
    __pycache__
  | \\.git
  | \\.venv
  | venv
  | backups
  | data/snapshots
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
skip_glob = ["__pycache__", ".git", ".venv", "venv", "backups", "data/snapshots"]
"""

        # Write config files
        try:
            with open(".flake8", "w") as f:
                f.write(flake8_config)
            print("  ✅ Created .flake8 configuration")

            with open("pyproject.toml", "w") as f:
                f.write(pyproject_config)
            print("  ✅ Created pyproject.toml configuration")

        except Exception as e:
            print(f"  ⚠️ Error creating config files: {e}")

    def find_python_files(self) -> List[str]:
        """Find all Python files to process"""
        python_files = []

        for root, dirs, files in os.walk("."):
            # Skip certain directories
            if any(
                skip_dir in root
                for skip_dir in ["__pycache__", ".git", "backups", "data/snapshots"]
            ):
                continue

            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        return python_files

    def run_linting(self, files: List[str]) -> Dict:
        """Run flake8 linting on Python files"""
        print(f"=== Running linting on {len(files)} files ===")

        try:
            result = subprocess.run(["flake8"] + files, capture_output=True, text=True)

            if result.stdout:
                issues = result.stdout.strip().split("\n")
                self.stats["linting_issues_found"] = len(issues)

                print(f"  ⚠️ Found {len(issues)} linting issues")

                # Show first 10 issues
                for issue in issues[:10]:
                    print(f"    {issue}")

                if len(issues) > 10:
                    print(f"    ... and {len(issues) - 10} more issues")

                return {"success": True, "issues": issues}
            else:
                print("  ✅ No linting issues found")
                return {"success": True, "issues": []}

        except Exception as e:
            print(f"  ❌ Linting failed: {e}")
            return {"success": False, "error": str(e)}

    def run_formatting(self, files: List[str]) -> Dict:
        """Run black formatting on Python files"""
        print(f"=== Running formatting on {len(files)} files ===")

        try:
            # Run black with --diff to see what would change
            diff_result = subprocess.run(
                ["black", "--diff", "--quiet"] + files, capture_output=True, text=True
            )

            if diff_result.stdout:
                print("  📝 Files need formatting")

                # Actually format the files
                format_result = subprocess.run(["black"] + files, capture_output=True, text=True)

                if format_result.returncode == 0:
                    # Count formatted files
                    if format_result.stderr:
                        formatted_count = len(
                            [
                                line
                                for line in format_result.stderr.split("\n")
                                if "reformatted" in line
                            ]
                        )
                        self.stats["formatting_issues_fixed"] = formatted_count
                        print(f"  ✅ Formatted {formatted_count} files")
                    else:
                        print("  ✅ Formatting completed")
                else:
                    print(f"  ⚠️ Some formatting issues: {format_result.stderr}")
            else:
                print("  ✅ All files already properly formatted")

            return {"success": True}

        except Exception as e:
            print(f"  ❌ Formatting failed: {e}")
            return {"success": False, "error": str(e)}

    def run_import_sorting(self, files: List[str]) -> Dict:
        """Run isort on Python files"""
        print(f"=== Running import sorting on {len(files)} files ===")

        try:
            result = subprocess.run(
                ["isort", "--diff", "--check-only"] + files, capture_output=True, text=True
            )

            if result.returncode != 0:
                print("  📝 Files need import sorting")

                # Actually sort the imports
                sort_result = subprocess.run(["isort"] + files, capture_output=True, text=True)

                if sort_result.returncode == 0:
                    print("  ✅ Import sorting completed")
                else:
                    print(f"  ⚠️ Some import sorting issues: {sort_result.stderr}")
            else:
                print("  ✅ All imports already properly sorted")

            return {"success": True}

        except Exception as e:
            print(f"  ❌ Import sorting failed: {e}")
            return {"success": False, "error": str(e)}

    def find_remaining_hardcoded_paths(self) -> List[Tuple[str, str, int]]:
        """Find any remaining hardcoded paths"""
        print("=== Scanning for remaining hardcoded paths ===")

        hardcoded_patterns = [
            r"/home/user/[a-zA-Z0-9_/-]*",
            r"C:\\\\[a-zA-Z0-9_\\\\-]*",
            r"C:/[a-zA-Z0-9_/-]*",
        ]

        issues = []

        try:
            # Use grep to find potential hardcoded paths
            result = subprocess.run(
                ["grep", "-r", "-n", "-E", "|".join(hardcoded_patterns), "--include=*.py", "."],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if ":" in line:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            file_path = parts[0]
                            line_num = parts[1]
                            content = parts[2]

                            # Filter out legitimate cases
                            if not any(
                                skip in content.lower()
                                for skip in [
                                    "comment",
                                    "#",
                                    "docstring",
                                    "example",
                                    "test",
                                    "path_manager",
                                    "get_velos_root",
                                    "fallback",
                                ]
                            ):
                                issues.append((file_path, content.strip(), int(line_num)))

                self.stats["hardcoded_paths_found"] = len(issues)
                print(f"  ⚠️ Found {len(issues)} potentially hardcoded paths")

                # Show first 5 issues
                for file_path, content, line_num in issues[:5]:
                    print(f"    {file_path}:{line_num} - {content[:60]}...")

                if len(issues) > 5:
                    print(f"    ... and {len(issues) - 5} more issues")
            else:
                print("  ✅ No hardcoded paths found")

        except Exception as e:
            print(f"  ❌ Path scanning failed: {e}")

        return issues

    def run_quality_improvements(self) -> Dict:
        """Run all code quality improvements"""
        start_time = time.time()

        print("VELOS Phase 5: Code Quality Improvements")
        print("=" * 50)

        # Step 1: Setup tools
        if not self.setup_code_quality_tools():
            return {"success": False, "error": "Failed to setup tools"}

        # Step 2: Find Python files
        python_files = self.find_python_files()
        self.stats["python_files_processed"] = len(python_files)
        print(f"\nFound {len(python_files)} Python files to process")

        # Step 3: Run linting
        linting_result = self.run_linting(python_files)

        # Step 4: Run formatting
        formatting_result = self.run_formatting(python_files)

        # Step 5: Run import sorting
        import_result = self.run_import_sorting(python_files)

        # Step 6: Check for hardcoded paths
        hardcoded_issues = self.find_remaining_hardcoded_paths()

        # Summary
        duration = time.time() - start_time

        print(f"\n" + "=" * 50)
        print("CODE QUALITY RESULTS:")
        print("=" * 50)
        print(f"Execution time: {duration:.2f} seconds")
        print(f"Python files processed: {self.stats['python_files_processed']}")
        print(f"Linting issues found: {self.stats['linting_issues_found']}")
        print(f"Files formatted: {self.stats['formatting_issues_fixed']}")
        print(f"Hardcoded paths found: {self.stats['hardcoded_paths_found']}")

        return {
            "success": True,
            "duration": duration,
            "stats": self.stats,
            "linting_result": linting_result,
            "hardcoded_issues": hardcoded_issues,
        }


def main():
    improver = CodeQualityImprover()
    result = improver.run_quality_improvements()

    if result["success"]:
        print(f"\n🎉 Code quality improvements completed!")
        if result["stats"]["linting_issues_found"] > 0:
            print(
                f"⚠️ {result['stats']['linting_issues_found']} linting issues found - review needed"
            )
        if result["stats"]["hardcoded_paths_found"] > 0:
            print(
                f"⚠️ {result['stats']['hardcoded_paths_found']} hardcoded paths found - review needed"
            )
    else:
        print(f"\n❌ Code quality improvements failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
