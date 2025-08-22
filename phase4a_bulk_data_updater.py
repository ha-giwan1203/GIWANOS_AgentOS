#!/usr/bin/env python3
"""
VELOS Phase 4A: Bulk Data File Path Updater
Systematically updates path references in large number of data files.
"""

import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Set


class BulkDataPathUpdater:
    """High-performance bulk updater for data file path references"""

    def __init__(self, dry_run: bool = False, max_workers: int = 4):
        self.dry_run = dry_run
        self.max_workers = max_workers
        self.updated_files = []
        self.errors = []
        self.stats = {
            "files_processed": 0,
            "files_updated": 0,
            "references_updated": 0,
            "errors": 0,
        }

    def find_data_files_with_paths(self) -> Dict[str, List[str]]:
        """Find data files containing C:\giwanos references"""
        print("=== Scanning for data files with path references ===")

        file_categories = {
            "json_data": [],
            "log_files": [],
            "session_files": [],
            "report_files": [],
            "snapshot_files": [],
            "other_data": [],
        }

        try:
            # Use find + grep for efficient scanning
            result = subprocess.run(
                [
                    "find",
                    ".",
                    "-name",
                    "*.json",
                    "-exec",
                    "grep",
                    "-l",
                    "C:\giwanos",
                    "{}",
                    ";",
                ],
                cwd="C:\giwanos",
                capture_output=True,
                text=True,
            )

            if result.stdout:
                json_files = result.stdout.strip().split("\n")

                for file_path in json_files:
                    if "session" in file_path:
                        file_categories["session_files"].append(file_path)
                    elif "report" in file_path:
                        file_categories["report_files"].append(file_path)
                    elif "log" in file_path:
                        file_categories["log_files"].append(file_path)
                    elif "snapshot" in file_path:
                        file_categories["snapshot_files"].append(file_path)
                    else:
                        file_categories["json_data"].append(file_path)

        except Exception as e:
            self.errors.append(f"File scanning error: {e}")

        # Report findings
        total_files = sum(len(files) for files in file_categories.values())
        print(f"Found {total_files} data files with path references:")
        for category, files in file_categories.items():
            if files:
                print(f"  {category}: {len(files)} files")

        return file_categories

    def analyze_path_patterns(self, file_path: str) -> Dict[str, int]:
        """Analyze path patterns in a file"""
        patterns = {
            "windows_paths": 0,
            "data_paths": 0,
            "config_paths": 0,
            "log_paths": 0,
            "other_paths": 0,
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Count different types of path references
            patterns["windows_paths"] = len(re.findall(r"C:\giwanos", content))
            patterns["data_paths"] = len(re.findall(r"C:\giwanos/data/", content))
            patterns["config_paths"] = len(re.findall(r"C:\giwanos/configs/", content))
            patterns["log_paths"] = len(re.findall(r"C:\giwanos/.*logs/", content))

        except Exception as e:
            self.errors.append(f"Pattern analysis error for {file_path}: {e}")

        return patterns

    def update_json_file_paths(self, file_path: str) -> bool:
        """Update path references in a JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Path replacement patterns
            replacements = [
                # Database paths
                (
                    r'"C:\giwanos/data/memory/velos\.db"',
                    '"C:\giwanos/data/memory/velos.db"',
                ),
                # General data paths
                (r'"C:\giwanos/data/([^"]+)"', r'"C:\giwanos/data/\1"'),
                # Config paths
                (r'"C:\giwanos/configs/([^"]+)"', r'"C:\giwanos/configs/\1"'),
                # Log paths
                (r'"C:\giwanos/([^"]*logs[^"]*)"', r'"C:\giwanos/\1"'),
                # General root paths
                (r'"C:\giwanos/([^"]+)"', r'"C:\giwanos/\1"'),
                # Handle escaped paths in JSON
                (r'"C:\\\\giwanos\\\\([^"]+)"', r'"C:\giwanos/\1"'),
            ]

            changes_made = False
            reference_count = 0

            for pattern, replacement in replacements:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    changes_made = True
                    reference_count += count

            # Write back if changed
            if changes_made:
                if not self.dry_run:
                    # Validate JSON before writing
                    try:
                        json.loads(content)  # Validate it's still valid JSON
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                    except json.JSONDecodeError:
                        print(f"⚠️ JSON validation failed for {file_path}, skipping")
                        return False

                self.stats["references_updated"] += reference_count
                return True

            return False

        except Exception as e:
            self.errors.append(f"JSON update error for {file_path}: {e}")
            self.stats["errors"] += 1
            return False

    def update_file_batch(self, file_paths: List[str]) -> Dict[str, int]:
        """Update a batch of files"""
        batch_stats = {"processed": 0, "updated": 0, "errors": 0}

        for file_path in file_paths:
            try:
                batch_stats["processed"] += 1

                if self.update_json_file_paths(file_path):
                    batch_stats["updated"] += 1
                    self.updated_files.append(file_path)

            except Exception as e:
                batch_stats["errors"] += 1
                self.errors.append(f"Batch update error for {file_path}: {e}")

        return batch_stats

    def update_files_parallel(self, files: List[str], category: str) -> Dict[str, int]:
        """Update files in parallel for better performance"""
        print(f"\n🔧 Updating {category} ({len(files)} files)...")

        if not files:
            return {"processed": 0, "updated": 0, "errors": 0}

        # Split files into batches for parallel processing
        batch_size = max(1, len(files) // self.max_workers)
        batches = [files[i : i + batch_size] for i in range(0, len(files), batch_size)]

        total_stats = {"processed": 0, "updated": 0, "errors": 0}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch jobs
            future_to_batch = {
                executor.submit(self.update_file_batch, batch): i for i, batch in enumerate(batches)
            }

            # Collect results
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_stats = future.result()
                    for key in total_stats:
                        total_stats[key] += batch_stats[key]

                    print(
                        f"  Batch {batch_num + 1}/{len(batches)}: {batch_stats['updated']}/{batch_stats['processed']} files updated"
                    )

                except Exception as e:
                    print(f"  Batch {batch_num + 1} failed: {e}")
                    total_stats["errors"] += 1

        print(f"  ✅ {category}: {total_stats['updated']}/{total_stats['processed']} files updated")
        return total_stats

    def create_backup_strategy(self, file_categories: Dict[str, List[str]]) -> bool:
        """Create backup strategy for critical data"""
        print("\n=== Creating backup strategy ===")

        # Identify critical files that should be backed up
        critical_categories = ["session_files", "report_files"]
        critical_files = []

        for category in critical_categories:
            critical_files.extend(file_categories.get(category, []))

        if critical_files:
            backup_dir = Path("C:\giwanos/backups/phase4a_" + str(int(time.time())))

            if not self.dry_run:
                backup_dir.mkdir(parents=True, exist_ok=True)

                # Create a manifest of files to backup
                manifest = {
                    "timestamp": int(time.time()),
                    "total_files": len(critical_files),
                    "categories": {cat: len(files) for cat, files in file_categories.items()},
                }

                with open(backup_dir / "backup_manifest.json", "w") as f:
                    json.dump(manifest, f, indent=2)

                print(f"✅ Backup directory created: {backup_dir}")
                print(f"   Critical files to monitor: {len(critical_files)}")
            else:
                print(f"🔍 Would create backup directory: {backup_dir}")
                print(f"   Critical files to backup: {len(critical_files)}")

        return True

    def run_bulk_update(self) -> Dict[str, any]:
        """Run complete bulk data file update"""
        print("VELOS Phase 4A: Bulk Data File Path Updates")
        print("=" * 60)

        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")

        start_time = time.time()

        # Step 1: Find files
        file_categories = self.find_data_files_with_paths()

        if not any(file_categories.values()):
            print("✅ No data files with path references found!")
            return {"total_files": 0, "updated_files": 0}

        # Step 2: Create backup strategy
        self.create_backup_strategy(file_categories)

        # Step 3: Update files by category (prioritized order)
        priority_order = [
            "log_files",  # Least critical, good for testing
            "other_data",  # General data files
            "snapshot_files",  # Snapshot data
            "report_files",  # Report files (more important)
            "session_files",  # Session data (most critical)
        ]

        for category in priority_order:
            if category in file_categories:
                category_stats = self.update_files_parallel(file_categories[category], category)

                # Update global stats
                for key in ["processed", "updated"]:
                    self.stats[f"files_{key}"] += category_stats[key]
                self.stats["errors"] += category_stats["errors"]

        # Step 4: Generate summary
        duration = time.time() - start_time

        print("\n" + "=" * 60)
        print("PHASE 4A BULK UPDATE RESULTS:")
        print("=" * 60)
        print(f"Execution time: {duration:.2f} seconds")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files updated: {self.stats['files_updated']}")
        print(f"Path references updated: {self.stats['references_updated']}")
        print(f"Errors encountered: {self.stats['errors']}")

        if self.errors:
            print(f"\n⚠️ Error details (first 5):")
            for error in self.errors[:5]:
                print(f"  {error}")

        success_rate = (self.stats["files_updated"] / max(1, self.stats["files_processed"])) * 100
        print(f"\n✅ Success rate: {success_rate:.1f}%")

        return {
            "duration": duration,
            "stats": self.stats,
            "updated_files": len(self.updated_files),
            "error_count": len(self.errors),
        }

    def verify_updates(self, sample_size: int = 10) -> bool:
        """Verify a sample of updated files"""
        print(f"\n=== Verifying {min(sample_size, len(self.updated_files))} updated files ===")

        if not self.updated_files:
            print("No files to verify")
            return True

        sample_files = self.updated_files[:sample_size]
        verification_passed = 0

        for file_path in sample_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check that C:\giwanos references are reduced
                old_refs = content.count("C:\giwanos")
                new_refs = content.count("C:\giwanos")

                if new_refs > 0:
                    verification_passed += 1
                    print(f"  ✅ {file_path}: {new_refs} new references")
                else:
                    print(f"  ⚠️ {file_path}: No new references found")

            except Exception as e:
                print(f"  ❌ {file_path}: Verification failed - {e}")

        success_rate = (verification_passed / len(sample_files)) * 100
        print(f"\nVerification success rate: {success_rate:.1f}%")

        return success_rate > 80


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="VELOS Phase 4A Bulk Data Path Updates")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be changed without modifying files"
    )
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--verify", action="store_true", help="Verify updates after completion")

    args = parser.parse_args()

    updater = BulkDataPathUpdater(dry_run=args.dry_run, max_workers=args.workers)

    try:
        # Run bulk update
        results = updater.run_bulk_update()

        # Verify if requested
        if args.verify and not args.dry_run:
            updater.verify_updates()

        # Return success/failure based on results
        if results["error_count"] > results["updated_files"] * 0.1:  # More than 10% errors
            print("\n❌ Too many errors encountered")
            return False
        else:
            print("\n🎉 Bulk update completed successfully!")
            return True

    except KeyboardInterrupt:
        print("\n⚠️ Update interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
