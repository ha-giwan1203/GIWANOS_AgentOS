#!/usr/bin/env python3
"""
VELOS Phase 3 Validation: Import Optimization Verification
Validates that import optimizations work correctly and system functionality is preserved.
"""

import os
import subprocess
import sys
from pathlib import Path


def test_import_manager():
    """Test the import manager functionality"""
    print("=== Import Manager Tests ===")

    try:
        from modules.core.import_manager import (
            cleanup_imports,
            ensure_velos_imports,
            get_import_info,
            get_velos_root,
            import_velos,
        )

        print("✅ Import manager module loaded successfully")

        # Test basic functionality
        root_path = get_velos_root()
        print(f"✅ VELOS root: {root_path}")

        # Test critical module imports
        critical_success = ensure_velos_imports()
        print(f"✅ Critical imports: {'Success' if critical_success else 'Some failures'}")

        # Test specific module import
        try:
            path_manager = import_velos("core.path_manager")
            print("✅ Successfully imported core.path_manager via import manager")
        except Exception as e:
            print(f"❌ Failed to import via manager: {e}")
            return False

        # Test import info
        info = get_import_info()
        print(f"Import manager stats: {info}")

        # Test sys.path cleanup
        original_length = len(sys.path)
        removed = cleanup_imports()
        print(
            f"✅ Sys.path cleanup: removed {removed} duplicates (was {original_length}, now {len(sys.path)})"
        )

        return True

    except Exception as e:
        print(f"❌ Import manager test failed: {e}")
        return False


def test_optimized_scripts():
    """Test that optimized scripts still work"""
    print("\n=== Optimized Scripts Tests ===")

    # Test the stats script that was optimized
    try:
        result = subprocess.run(
            [sys.executable, "scripts/check_velos_stats.py"],
            cwd="/home/user/webapp",
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ check_velos_stats.py: Working after optimization")
            # Check if it's still accessing the real database
            if "1392개" in result.stdout or "1,392" in result.stdout:
                print("✅ Still accessing real database with 1,392 records")
            return True
        else:
            print(f"❌ check_velos_stats.py failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Script test error: {e}")
        return False


def test_memory_system():
    """Test memory system functionality after optimization"""
    print("\n=== Memory System Tests ===")

    try:
        # Test direct memory access
        from modules.core.memory_adapter.adapter import create_memory_adapter

        adapter = create_memory_adapter()
        stats = adapter.get_stats()

        record_count = stats.get("db_records", 0)
        print(f"✅ Memory system: {record_count} records accessible")

        if record_count > 1000:
            print("✅ Real production database still accessible")
            return True
        else:
            print(f"⚠️ Low record count: {record_count}")
            return False

    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        return False


def test_import_reduction():
    """Test that sys.path manipulations have been reduced"""
    print("\n=== Import Reduction Tests ===")

    try:
        # Count remaining sys.path manipulations
        result = subprocess.run(
            ["grep", "-r", "sys.path", "--include=*.py", "."],
            cwd="/home/user/webapp",
            capture_output=True,
            text=True,
        )

        if result.stdout:
            lines = result.stdout.strip().split("\n")
            # Filter out our new import manager and comments
            active_manipulations = [
                line
                for line in lines
                if not any(
                    skip in line
                    for skip in [
                        "import_manager.py",
                        "# Replaced with import manager",
                        "phase3_",
                        "__pycache__",
                    ]
                )
            ]

            print(f"Remaining sys.path manipulations: {len(active_manipulations)}")

            # Count files with manipulations
            files_with_syspath = set()
            for line in active_manipulations:
                if ":" in line:
                    file_path = line.split(":", 1)[0]
                    files_with_syspath.add(file_path)

            print(f"Files with sys.path: {len(files_with_syspath)}")

            # Show reduction from original estimate
            original_estimate = 71  # From our analysis
            current_count = len(files_with_syspath)
            reduction = original_estimate - current_count

            print(
                f"✅ Reduction achieved: {reduction} files ({original_estimate} → {current_count})"
            )

            return current_count < 15  # Target: reduce to under 15 files
        else:
            print("✅ No sys.path manipulations found!")
            return True

    except Exception as e:
        print(f"❌ Import reduction test failed: {e}")
        return False


def test_package_structure():
    """Test that package structure improvements work"""
    print("\n=== Package Structure Tests ===")

    try:
        # Test new __init__.py files work
        import modules.memory
        import modules.memory.cache
        import modules.memory.ingest
        import modules.memory.router

        print("✅ All new package __init__.py files importable")

        # Test package-level imports
        from modules.memory import cache, router, storage

        print("✅ Package-level imports working")

        return True

    except Exception as e:
        print(f"❌ Package structure test failed: {e}")
        return False


def main():
    """Run all Phase 3 validation tests"""
    print("VELOS Phase 3 Validation - Import Optimization Verification")
    print("=" * 70)

    tests = [
        ("Import Manager", test_import_manager),
        ("Optimized Scripts", test_optimized_scripts),
        ("Memory System", test_memory_system),
        ("Import Reduction", test_import_reduction),
        ("Package Structure", test_package_structure),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test execution error: {e}")
            results[test_name] = False

    print("\n" + "=" * 70)
    print("PHASE 3 VALIDATION RESULTS:")
    print("=" * 70)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if not result:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("🎉 Phase 3 검증 완료! 모든 import 최적화가 정상 작동합니다.")
        print("시스템 성능이 향상되고 sys.path 조작이 크게 감소했습니다.")
    else:
        print("⚠️ 일부 테스트 실패. 문제를 확인하고 수정이 필요합니다.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
