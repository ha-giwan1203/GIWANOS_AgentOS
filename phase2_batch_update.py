#!/usr/bin/env python3
"""
VELOS Phase 2 Batch Update: Systematic path reference standardization
Updates multiple files to use the new path manager for cross-platform compatibility.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set

class VelosPathUpdater:
    """Batch updater for VELOS path references"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.updated_files = []
        self.errors = []
        
    def find_files_with_path_refs(self, directories: List[str]) -> List[str]:
        """Find files containing C:/giwanos references"""
        files = []
        for directory in directories:
            try:
                result = subprocess.run(
                    ["grep", "-rl", "C:/giwanos", "--include=*.py", directory],
                    cwd="/home/user/webapp", capture_output=True, text=True
                )
                if result.stdout.strip():
                    dir_files = result.stdout.strip().split('\n')
                    files.extend(dir_files)
            except Exception as e:
                self.errors.append(f"Error searching {directory}: {e}")
        
        return list(set(files))  # Remove duplicates
    
    def update_hardcoded_paths(self, file_path: str) -> bool:
        """Update hardcoded C:/giwanos paths in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Pattern 1: Direct C:/giwanos references
            patterns = [
                # Database path patterns
                (r'["\']C:/giwanos/data/memory/velos\.db["\']', 
                 'get_db_path() if "get_db_path" in locals() else "C:/giwanos/data/memory/velos.db"'),
                
                # General data paths
                (r'["\']C:/giwanos/data/([^"\']+)["\']', 
                 r'get_data_path("\1") if "get_data_path" in locals() else "C:/giwanos/data/\1"'),
                
                # Config paths
                (r'["\']C:/giwanos/configs/([^"\']+)["\']', 
                 r'get_config_path("\1") if "get_config_path" in locals() else "C:/giwanos/configs/\1"'),
                
                # Root path references
                (r'ROOT\s*=\s*["\']C:/giwanos["\']', 
                 'ROOT = get_velos_root() if "get_velos_root" in locals() else "C:/giwanos"'),
            ]
            
            changes_made = False
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    changes_made = True
            
            # Add import statement if changes were made and not already present
            if changes_made and "from modules.core.path_manager import" not in content:
                # Find a good place to add the import
                lines = content.split('\n')
                import_added = False
                
                for i, line in enumerate(lines):
                    # Add after existing imports
                    if line.startswith('import ') or line.startswith('from '):
                        continue
                    elif not line.strip() or line.startswith('#'):
                        continue
                    else:
                        # Insert import before this line
                        import_line = "# Path manager imports (Phase 2 standardization)"
                        try_import = """try:
    from modules.core.path_manager import get_velos_root, get_data_path, get_config_path, get_db_path
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root(): return "C:/giwanos"
    def get_data_path(*parts): return os.path.join("C:/giwanos", "data", *parts)
    def get_config_path(*parts): return os.path.join("C:/giwanos", "configs", *parts)
    def get_db_path(): return "C:/giwanos/data/memory/velos.db"
"""
                        lines.insert(i, import_line)
                        lines.insert(i + 1, try_import)
                        import_added = True
                        break
                
                if import_added:
                    content = '\n'.join(lines)
            
            # Write back if changed
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                self.updated_files.append(file_path)
                return True
            
            return False
            
        except Exception as e:
            self.errors.append(f"Error updating {file_path}: {e}")
            return False
    
    def update_environment_variable_names(self, file_path: str) -> bool:
        """Update environment variable references to use consistent naming"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Standardize environment variable names
            patterns = [
                (r'os\.getenv\(["\']VELOS_DB["\']\)', 'os.getenv("VELOS_DB_PATH")'),
                (r'os\.environ\.get\(["\']VELOS_DB["\']\)', 'os.environ.get("VELOS_DB_PATH")'),
                (r'os\.environ\[["\']VELOS_DB["\']\]', 'os.environ["VELOS_DB_PATH"]'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                return True
            
            return False
            
        except Exception as e:
            self.errors.append(f"Error updating env vars in {file_path}: {e}")
            return False
    
    def update_files_in_directory(self, directory: str) -> Dict[str, int]:
        """Update all files in a directory"""
        print(f"\n🔧 Updating files in {directory}...")
        
        files = self.find_files_with_path_refs([directory])
        stats = {"total": len(files), "updated": 0, "env_updated": 0}
        
        for file_path in files:
            if self.update_hardcoded_paths(file_path):
                stats["updated"] += 1
                print(f"  ✅ Updated paths: {file_path}")
            
            if self.update_environment_variable_names(file_path):
                stats["env_updated"] += 1
                print(f"  ✅ Updated env vars: {file_path}")
        
        return stats
    
    def run_phase2_update(self) -> Dict[str, any]:
        """Run complete Phase 2 path standardization"""
        print("VELOS Phase 2 Batch Update - Path Standardization")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
        
        # Priority directories for updating
        priority_dirs = [
            "scripts",
            "modules/core", 
            "modules/memory",
            "modules/automation",
            "configs",
        ]
        
        total_stats = {"directories": 0, "total_files": 0, "updated_files": 0, "env_updates": 0}
        
        for directory in priority_dirs:
            if os.path.exists(directory):
                stats = self.update_files_in_directory(directory)
                total_stats["directories"] += 1
                total_stats["total_files"] += stats["total"]
                total_stats["updated_files"] += stats["updated"] 
                total_stats["env_updates"] += stats["env_updated"]
        
        # Report results
        print("\n" + "=" * 60)
        print("PHASE 2 BATCH UPDATE RESULTS:")
        print("=" * 60)
        print(f"Directories processed: {total_stats['directories']}")
        print(f"Total files scanned: {total_stats['total_files']}")
        print(f"Files with path updates: {total_stats['updated_files']}")
        print(f"Files with env var updates: {total_stats['env_updates']}")
        
        if self.errors:
            print(f"\n⚠️ Errors encountered: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more errors")
        
        return total_stats

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VELOS Phase 2 Path Standardization")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    parser.add_argument("--directory", "-d", action="append", help="Specific directory to update")
    
    args = parser.parse_args()
    
    updater = VelosPathUpdater(dry_run=args.dry_run)
    
    if args.directory:
        # Update specific directories
        for directory in args.directory:
            updater.update_files_in_directory(directory)
    else:
        # Run full Phase 2 update
        results = updater.run_phase2_update()
    
    return updater

if __name__ == "__main__":
    updater = main()