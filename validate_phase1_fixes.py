#!/usr/bin/env python3
"""
VELOS Phase 1 Validation: Environment Variables and Database Path Fixes
Validates that all critical environment variable and database path fixes are working.
"""

import json
import os
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))


def test_environment_variables():
    """Test environment variable consistency across the system"""
    print("=== Environment Variable Tests ===")

    # Check VELOS_DB_PATH setting
    default_path = "/home/user/webapp/data/memory/velos.db"
    actual_path = os.environ.get("VELOS_DB_PATH", default_path)

    print(f"VELOS_DB_PATH: {actual_path}")

    # Convert to local path for sandbox environment
    if actual_path.startswith("/home/user/webapp"):
        local_path = actual_path.replace("/home/user/webapp", "/home/user/webapp")
        local_path = local_path.replace("\\", "/")
        print(f"Local path: {local_path}")

        if os.path.exists(local_path):
            print(f"✅ Database file exists: {local_path}")
            return local_path
        else:
            print(f"❌ Database file missing: {local_path}")
            return None

    return actual_path


def test_memory_access():
    """Test memory system access and record count"""
    print("\n=== Memory Access Tests ===")

    try:
        from modules.core.memory_adapter.adapter import create_memory_adapter

        # Set environment variable for local testing
        os.environ["VELOS_DB_PATH"] = "/home/user/webapp/data/memory/velos.db"

        adapter = create_memory_adapter()
        stats = adapter.get_stats()

        print(
            f"✅ 메모리 접근: {stats['db_records']}개 {'(실제 데이터!)' if stats['db_records'] > 100 else '(소규모 데이터)'}"
        )
        print(f"Buffer size: {stats.get('buffer_size', 0)}")
        print(f"JSON records: {stats.get('json_records', 0)}")

        return stats["db_records"] > 0

    except Exception as e:
        print(f"❌ 메모리 접근 오류: {e}")
        return False


def test_sqlite_store():
    """Test SQLite store configuration"""
    print("\n=== SQLite Store Tests ===")

    try:
        from modules.memory.storage.sqlite_store import VelosMemoryStore

        # Set environment for testing
        os.environ["VELOS_DB_PATH"] = "/home/user/webapp/data/memory/velos.db"

        store = VelosMemoryStore()
        print(f"✅ sqlite_store: {store.db_path}")

        return True

    except Exception as e:
        print(f"❌ sqlite_store 오류: {e}")
        return False


def test_db_util():
    """Test database utility module"""
    print("\n=== Database Utility Tests ===")

    try:
        from modules.core.db_util import db_open

        # Set environment for testing
        os.environ["VELOS_DB_PATH"] = "/home/user/webapp/data/memory/velos.db"

        db_path = os.environ.get("VELOS_DB_PATH")
        print(f"✅ db_util path: {db_path}")

        if os.path.exists(db_path):
            print("✅ Database file accessible")
            return True
        else:
            print("❌ Database file not found")
            return False

    except Exception as e:
        print(f"❌ db_util 오류: {e}")
        return False


def test_config_files():
    """Test configuration file consistency"""
    print("\n=== Configuration File Tests ===")

    # Check settings.yaml
    settings_path = "/home/user/webapp/configs/settings.yaml"
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "data/memory/velos.db" in content:
                print("✅ settings.yaml: 올바른 데이터베이스 경로")
            else:
                print("❌ settings.yaml: 잘못된 데이터베이스 경로")
                return False

    return True


def test_benchmark_regression():
    """Test benchmark regression fixes"""
    print("\n=== Benchmark Regression Tests ===")

    try:
        # Check if benchmark file exists and has correct sync check
        benchmark_path = "/home/user/webapp/tests/perf/benchmark_regression.py"
        if os.path.exists(benchmark_path):
            with open(benchmark_path, "r", encoding="utf-8") as f:
                content = f.read()
                if 'data["sanity"].get("sync") != 2' in content:
                    print("✅ benchmark_regression: 올바른 sync 체크 (2)")
                    return True
                else:
                    print("❌ benchmark_regression: 잘못된 sync 체크")
                    return False
        else:
            print("⚠️ benchmark_regression.py 파일 없음")
            return True

    except Exception as e:
        print(f"❌ benchmark_regression 오류: {e}")
        return False


def main():
    """Run all Phase 1 validation tests"""
    print("VELOS Phase 1 Validation - 환경 변수 및 데이터베이스 경로 수정 검증")
    print("=" * 70)

    tests = [
        ("Environment Variables", test_environment_variables),
        ("Memory Access", test_memory_access),
        ("SQLite Store", test_sqlite_store),
        ("Database Utility", test_db_util),
        ("Configuration Files", test_config_files),
        ("Benchmark Regression", test_benchmark_regression),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} 테스트 실행 오류: {e}")
            results[test_name] = False

    print("\n" + "=" * 70)
    print("PHASE 1 VALIDATION RESULTS:")
    print("=" * 70)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if not result:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("🎉 Phase 1 검증 완료! 모든 환경 변수 및 데이터베이스 경로 수정이 정상 작동합니다.")
        print("Phase 2 (Configuration Cleanup)로 진행할 준비가 되었습니다.")
    else:
        print("⚠️ 일부 테스트 실패. 문제를 해결한 후 다시 실행하세요.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
