#!/usr/bin/env python3
"""
VELOS Phase 4A: Manual Path Updater (Robust Version)
Handles all file types including those with JSON validation issues
"""

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple


class ManualPathUpdater:
    """Robust path updater that handles all file types and encoding issues"""

    def __init__(self):
        self.updated_files = []
        self.failed_files = []
        self.stats = {"processed": 0, "updated": 0, "failed": 0, "path_replacements": 0}

    def find_all_files_with_paths(self) -> List[str]:
        """Find all files containing Windows path references"""
        print("=== Finding all files with Windows path references ===")

        # Use grep to find all files with Windows paths
        try:
            result = subprocess.run(
                [
                    "grep",
                    "-r",
                    "-l",
                    "--include=*.json",
                    "--include=*.py",
                    "--include=*.txt",
                    "--include=*.md",
                    "--include=*.yaml",
                    "--include=*.yml",
                    "C:\giwanos",
                    ".",
                ],
                cwd="C:\giwanos",
                capture_output=True,
                text=True,
            )

            if result.stdout:
                files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
                print(f"Found {len(files)} files with Windows path references")
                return files
            else:
                print("No files found with Windows path references")
                return []

        except Exception as e:
            print(f"Error finding files: {e}")
            return []

    def update_json_file(self, file_path: str) -> bool:
        """Update JSON file with proper BOM handling"""
        try:
            # Try to read with BOM handling
            encodings = ["utf-8-sig", "utf-8", "utf-16", "cp1252"]
            content = None
            used_encoding = "utf-8"

            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                print(f"  ❌ Could not read {file_path} with any encoding")
                return False

            # Count replacements
            original_content = content
            replacements = 0

            # Replace Windows paths
            patterns = [
                (r"C:\giwanos", "C:\giwanos"),
                (r"C:\\giwanos", "C:\giwanos"),
                (r"C:/Users/User/venvs/velos/Scripts/python\.exe", "/usr/bin/python3"),
                (r"C:\\Users\\User\\venvs\\velos\\Scripts\\python\.exe", "/usr/bin/python3"),
                (r"/tmp", "/tmp"),
                (r"C:\\WINDOWS\\system32", "/tmp"),
            ]

            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    replacements += len(re.findall(pattern, content, re.IGNORECASE))
                    content = new_content

            if replacements > 0:
                # Try to parse as JSON to validate
                try:
                    json.loads(content)
                    is_valid_json = True
                except json.JSONDecodeError as e:
                    # If it's not valid JSON after replacement, try to fix common issues
                    print(f"  ⚠️ JSON validation failed for {file_path}: {e}")
                    is_valid_json = False

                if is_valid_json or file_path.endswith(".json"):
                    # Write back without BOM
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    print(f"  ✅ Updated {file_path} ({replacements} replacements)")
                    self.stats["path_replacements"] += replacements
                    return True
                else:
                    print(f"  ❌ Skipped {file_path} due to JSON validation issues")
                    return False
            else:
                print(f"  ➖ No changes needed for {file_path}")
                return True

        except Exception as e:
            print(f"  ❌ Error updating {file_path}: {e}")
            return False

    def update_text_file(self, file_path: str) -> bool:
        """Update non-JSON text files"""
        try:
            # Read file content
            encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                print(f"  ❌ Could not read {file_path}")
                return False

            original_content = content
            replacements = 0

            # Replace Windows paths
            patterns = [
                (r"C:\giwanos", "C:\giwanos"),
                (r"C:\\giwanos", "C:\giwanos"),
                (r"C:/Users/User/venvs/velos/Scripts/python\.exe", "/usr/bin/python3"),
                (r"C:\\Users\\User\\venvs\\velos\\Scripts\\python\.exe", "/usr/bin/python3"),
                (r"/tmp", "/tmp"),
                (r"C:\\WINDOWS\\system32", "/tmp"),
            ]

            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    replacements += len(re.findall(pattern, content, re.IGNORECASE))
                    content = new_content

            if replacements > 0:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"  ✅ Updated {file_path} ({replacements} replacements)")
                self.stats["path_replacements"] += replacements
                return True
            else:
                print(f"  ➖ No changes needed for {file_path}")
                return True

        except Exception as e:
            print(f"  ❌ Error updating {file_path}: {e}")
            return False

    def update_file(self, file_path: str) -> bool:
        """Update a single file based on its type"""
        self.stats["processed"] += 1

        if file_path.endswith(".json"):
            success = self.update_json_file(file_path)
        else:
            success = self.update_text_file(file_path)

        if success:
            self.stats["updated"] += 1
            self.updated_files.append(file_path)
        else:
            self.stats["failed"] += 1
            self.failed_files.append(file_path)

        return success

    def run_manual_update(self) -> Dict:
        """Run the manual path update process"""
        start_time = time.time()

        print("VELOS Phase 4A: Manual Path Updates (Robust Version)")
        print("=" * 60)

        # Find all files
        files_to_update = self.find_all_files_with_paths()

        if not files_to_update:
            print("No files found to update")
            return {"duration": 0, "stats": self.stats}

        print(f"\n=== Processing {len(files_to_update)} files ===")

        # Process each file
        for i, file_path in enumerate(files_to_update, 1):
            if i % 50 == 0:
                print(f"\nProgress: {i}/{len(files_to_update)} files processed")

            self.update_file(file_path)

        # Summary
        duration = time.time() - start_time
        print(f"\n" + "=" * 60)
        print("MANUAL UPDATE RESULTS:")
        print("=" * 60)
        print(f"Execution time: {duration:.2f} seconds")
        print(f"Files processed: {self.stats['processed']}")
        print(f"Files updated: {self.stats['updated']}")
        print(f"Files failed: {self.stats['failed']}")
        print(f"Total path replacements: {self.stats['path_replacements']}")

        success_rate = (self.stats["updated"] / max(1, self.stats["processed"])) * 100
        print(f"Success rate: {success_rate:.1f}%")

        if self.failed_files:
            print(f"\n⚠️ Failed files (first 10):")
            for failed_file in self.failed_files[:10]:
                print(f"  {failed_file}")

        return {
            "duration": duration,
            "stats": self.stats,
            "updated_files": len(self.updated_files),
            "failed_files": len(self.failed_files),
        }


def main():
    updater = ManualPathUpdater()
    result = updater.run_manual_update()

    if result["stats"]["updated"] > 0:
        print(f"\n🎉 Successfully updated {result['stats']['updated']} files!")
    else:
        print(f"\n⚠️ No files were updated. Check for issues.")


if __name__ == "__main__":
    main()
