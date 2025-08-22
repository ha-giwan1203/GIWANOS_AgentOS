#!/usr/bin/env python3
"""
VELOS Phase 4B: Import Manager Migration
Convert remaining files to use import_manager instead of direct sys.path manipulation
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, List


class ImportManagerMigrator:
    """Migrates files to use import_manager instead of direct sys.path"""

    def __init__(self):
        self.updated_files = []
        self.skipped_files = []
        self.stats = {"processed": 0, "updated": 0, "skipped": 0, "conversions": 0}

        # Files that should skip migration (test files, import_manager itself, etc.)
        self.skip_patterns = [
            "test_",  # Test files can use direct sys.path
            "import_manager.py",  # The import_manager itself
            "__init__.py",  # Some __init__.py files may need direct control
        ]

    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped from migration"""
        file_name = os.path.basename(file_path)
        return any(pattern in file_name for pattern in self.skip_patterns)

    def find_files_needing_migration(self) -> List[str]:
        """Find Python files that still use direct sys.path manipulation"""
        print("=== Finding files needing import manager migration ===")

        files = []
        for root, dirs, filenames in os.walk("."):
            # Skip certain directories
            if any(skip_dir in root for skip_dir in ["__pycache__", ".git", "backups"]):
                continue

            for filename in filenames:
                if filename.endswith(".py"):
                    file_path = os.path.join(root, filename)

                    # Check if file has sys.path manipulation
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        if re.search(r"sys\.path\.(?:append|insert)", content):
                            if not self.should_skip_file(file_path):
                                files.append(file_path)
                    except Exception as e:
                        print(f"  ⚠️ Error reading {file_path}: {e}")

        print(f"Found {len(files)} files needing migration")
        return files

    def migrate_file_imports(self, file_path: str) -> bool:
        """Migrate a single file to use import_manager"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            conversions = 0

            # Pattern 1: sys.path.append/insert patterns
            sys_path_patterns = [
                # Common patterns
                (
                    r"import sys\s*\n.*?sys\.path\.(?:append|insert)\([^)]+\)",
                    "from modules.core.import_manager import ImportManager\nImportManager.setup_imports()",
                ),
                # Single line sys.path operations
                (r'sys\.path\.append\([\'"][^\'"]*[\'\"]\)', "# Migrated to import_manager"),
                (r'sys\.path\.insert\(0,\s*[\'"][^\'"]*[\'\"]\)', "# Migrated to import_manager"),
            ]

            # Apply basic patterns
            for pattern, replacement in sys_path_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
                    conversions += 1

            # More sophisticated replacement for complex cases
            # Look for sys import + sys.path usage blocks
            sys_import_pattern = r"^import sys\s*$"
            sys_path_pattern = r"^sys\.path\.(?:append|insert)\([^)]+\)\s*$"

            lines = content.split("\n")
            new_lines = []
            i = 0
            import_manager_added = False

            while i < len(lines):
                line = lines[i].strip()

                # Check for sys import followed by sys.path usage
                if re.match(sys_import_pattern, line):
                    # Look ahead for sys.path usage
                    j = i + 1
                    found_sys_path = False
                    sys_path_lines = []

                    while j < len(lines) and (
                        not lines[j].strip()
                        or lines[j].startswith("#")
                        or re.match(sys_path_pattern, lines[j].strip())
                    ):
                        if re.match(sys_path_pattern, lines[j].strip()):
                            found_sys_path = True
                            sys_path_lines.append(j)
                        j += 1

                    if found_sys_path and not import_manager_added:
                        # Replace with import_manager
                        new_lines.append("from modules.core.import_manager import ImportManager")
                        new_lines.append("ImportManager.setup_imports()")
                        import_manager_added = True
                        conversions += 1

                        # Skip the sys.path lines
                        i = j
                        continue

                new_lines.append(lines[i])
                i += 1

            if conversions > 0:
                content = "\n".join(new_lines)

            # Final cleanup: remove standalone sys imports if no longer needed
            if import_manager_added:
                # Remove standalone sys imports that are only used for path manipulation
                content = re.sub(
                    r"^import sys\s*\n(?=(?:(?!sys\.).)*(?:from modules\.core\.import_manager|ImportManager))",
                    "",
                    content,
                    flags=re.MULTILINE,
                )

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"  ✅ Updated {file_path} ({conversions} conversions)")
                self.stats["conversions"] += conversions
                return True
            else:
                print(f"  ➖ No changes needed for {file_path}")
                return True

        except Exception as e:
            print(f"  ❌ Error migrating {file_path}: {e}")
            return False

    def run_migration(self) -> Dict:
        """Run the import manager migration"""
        start_time = time.time()

        print("VELOS Phase 4B: Import Manager Migration")
        print("=" * 50)

        # Find files needing migration
        files_to_migrate = self.find_files_needing_migration()

        if not files_to_migrate:
            print("No files found needing migration")
            return {"duration": 0, "stats": self.stats}

        print(f"\n=== Processing {len(files_to_migrate)} files ===")

        # Process each file
        for file_path in files_to_migrate:
            self.stats["processed"] += 1

            if self.migrate_file_imports(file_path):
                self.stats["updated"] += 1
                self.updated_files.append(file_path)
            else:
                self.stats["skipped"] += 1
                self.skipped_files.append(file_path)

        # Summary
        duration = time.time() - start_time

        print(f"\n" + "=" * 50)
        print("IMPORT MIGRATION RESULTS:")
        print("=" * 50)
        print(f"Execution time: {duration:.2f} seconds")
        print(f"Files processed: {self.stats['processed']}")
        print(f"Files updated: {self.stats['updated']}")
        print(f"Files skipped: {self.stats['skipped']}")
        print(f"Total conversions: {self.stats['conversions']}")

        success_rate = (self.stats["updated"] / max(1, self.stats["processed"])) * 100
        print(f"Success rate: {success_rate:.1f}%")

        if self.skipped_files:
            print(f"\n⚠️ Skipped files:")
            for skipped_file in self.skipped_files:
                print(f"  {skipped_file}")

        return {"duration": duration, "stats": self.stats, "updated_files": len(self.updated_files)}


def main():
    migrator = ImportManagerMigrator()
    result = migrator.run_migration()

    if result["stats"]["updated"] > 0:
        print(f"\n🎉 Successfully migrated {result['stats']['updated']} files to import_manager!")
    else:
        print(f"\n⚠️ No files were migrated.")


if __name__ == "__main__":
    main()
