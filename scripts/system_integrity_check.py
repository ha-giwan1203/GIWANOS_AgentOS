# [ACTIVE] VELOS 시스템 무결성 체크 - 시스템 무결성 검증
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문
"판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

VELOS 시스템 무결성 체크
- 핵심 파일들의 존재 여부 확인
- 데이터베이스 무결성 검증
- 설정 파일 유효성 검사
"""

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# VELOS 루트 경로
VELOS_ROOT = Path(r"C:\giwanos")
DATA_DIR = VELOS_ROOT / "data"
CONFIGS_DIR = VELOS_ROOT / "configs"
SCRIPTS_DIR = VELOS_ROOT / "scripts"
MODULES_DIR = VELOS_ROOT / "modules"


class SystemIntegrityChecker:
    """시스템 무결성 검증기"""

    def __init__(self):
        self.root = VELOS_ROOT
        self.data_dir = DATA_DIR
        self.configs_dir = CONFIGS_DIR
        self.scripts_dir = SCRIPTS_DIR
        self.modules_dir = MODULES_DIR
        self.errors = []
        self.warnings = []

    def check_core_directories(self) -> bool:
        """핵심 디렉토리 존재 여부 확인"""
        print("🔍 핵심 디렉토리 확인...")

        required_dirs = [
            self.root,
            self.data_dir,
            self.configs_dir,
            self.scripts_dir,
            self.modules_dir,
            self.data_dir / "memory",
            self.data_dir / "logs",
            self.data_dir / "reports",
            self.data_dir / "snapshots",
            self.modules_dir / "core",
            self.modules_dir / "utils",
        ]

        all_exist = True
        for dir_path in required_dirs:
            if dir_path.exists():
                print(f"  ✅ {dir_path.name}/")
            else:
                print(f"  ❌ {dir_path.name}/ - 없음")
                self.errors.append(f"필수 디렉토리 없음: {dir_path}")
                all_exist = False

        return all_exist

    def check_core_files(self) -> bool:
        """핵심 파일 존재 여부 확인"""
        print("\n🔍 핵심 파일 확인...")

        required_files = [
            self.data_dir / "velos.db",
            self.configs_dir / "settings.yaml",
            self.configs_dir / "__init__.py",
            self.scripts_dir / "velos_master_scheduler.py",
            self.scripts_dir / "Start-Velos.ps1",
            self.modules_dir / "__init__.py",
            self.modules_dir / "core" / "__init__.py",
        ]

        all_exist = True
        for file_path in required_files:
            if file_path.exists():
                print(f"  ✅ {file_path.name}")
            else:
                print(f"  ❌ {file_path.name} - 없음")
                self.errors.append(f"필수 파일 없음: {file_path}")
                all_exist = False

        return all_exist

    def check_database_integrity(self) -> bool:
        """데이터베이스 무결성 확인"""
        print("\n🔍 데이터베이스 무결성 확인...")

        db_path = self.data_dir / "velos.db"
        if not db_path.exists():
            print("  ❌ velos.db 파일 없음")
            self.errors.append("데이터베이스 파일 없음")
            return False

        try:
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()

            # 테이블 존재 여부 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["memory", "memory_fts"]
            missing_tables = [table for table in required_tables if table not in tables]

            if missing_tables:
                print(f"  ❌ 누락된 테이블: {missing_tables}")
                self.errors.append(f"누락된 테이블: {missing_tables}")
                conn.close()
                return False
            else:
                print("  ✅ 모든 필수 테이블 존재")

            # 데이터 개수 확인
            cursor.execute("SELECT COUNT(*) FROM memory")
            memory_count = cursor.fetchone()[0]
            print(f"  📊 메모리 레코드 수: {memory_count}")

            if memory_count == 0:
                self.warnings.append("메모리 테이블이 비어있음")

            conn.close()
            return True

        except Exception as e:
            print(f"  ❌ 데이터베이스 오류: {e}")
            self.errors.append(f"데이터베이스 오류: {e}")
            return False

    def check_settings_validity(self) -> bool:
        """설정 파일 유효성 확인"""
        print("\n🔍 설정 파일 유효성 확인...")

        settings_path = self.configs_dir / "settings.yaml"
        if not settings_path.exists():
            print("  ❌ settings.yaml 파일 없음")
            self.errors.append("설정 파일 없음")
            return False

        try:
            import yaml

            with open(settings_path, "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f)

            required_keys = ["root", "database", "logging"]
            missing_keys = [key for key in required_keys if key not in settings]

            if missing_keys:
                print(f"  ❌ 누락된 설정 키: {missing_keys}")
                self.errors.append(f"누락된 설정 키: {missing_keys}")
                return False
            else:
                print("  ✅ 설정 파일 구조 정상")
                return True

        except Exception as e:
            print(f"  ❌ 설정 파일 오류: {e}")
            self.errors.append(f"설정 파일 오류: {e}")
            return False

    def check_python_syntax(self) -> bool:
        """Python 파일 구문 검사"""
        print("\n🔍 Python 파일 구문 검사...")

        python_files = [
            self.scripts_dir / "velos_master_scheduler.py",
            self.scripts_dir / "notion_memory_integrated.py",
            self.scripts_dir / "check_environment_integrated.py",
            self.configs_dir / "__init__.py",
            self.modules_dir / "__init__.py",
        ]

        all_valid = True
        for file_path in python_files:
            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    compile(f.read(), str(file_path), "exec")
                print(f"  ✅ {file_path.name}")
            except Exception as e:
                print(f"  ❌ {file_path.name} - 구문 오류: {e}")
                self.errors.append(f"Python 구문 오류 {file_path.name}: {e}")
                all_valid = False

        return all_valid

    def check_file_hashes(self) -> bool:
        """파일 해시 무결성 확인"""
        print("\n🔍 파일 해시 무결성 확인...")

        hash_file = self.configs_dir / "security" / "guard_hashes.json"
        if not hash_file.exists():
            print("  ⚠️ 해시 파일 없음 - 건너뜀")
            return True

        try:
            with open(hash_file, "r", encoding="utf-8-sig") as f:
                hash_data = json.load(f)

            all_valid = True
            for file_info in hash_data.get("files", []):
                file_path = Path(file_info["path"])
                expected_hash = file_info["sha256"]

                if not file_path.exists():
                    print(f"  ❌ {file_path.name} - 파일 없음")
                    self.errors.append(f"해시 파일에서 참조하는 파일 없음: {file_path}")
                    all_valid = False
                    continue

                with open(file_path, "rb") as f:
                    content = f.read()
                actual_hash = hashlib.sha256(content).hexdigest()

                if actual_hash != expected_hash:
                    print(f"  ❌ {file_path.name} - 해시 불일치")
                    self.errors.append(f"파일 해시 불일치: {file_path}")
                    all_valid = False
                else:
                    print(f"  ✅ {file_path.name}")

            return all_valid

        except Exception as e:
            print(f"  ❌ 해시 검증 오류: {e}")
            self.errors.append(f"해시 검증 오류: {e}")
            return False

    def run_full_check(self) -> Dict[str, any]:
        """전체 무결성 검사 실행"""
        print("🔍 VELOS 시스템 무결성 검사 시작")
        print("=" * 50)

        results = {
            "core_directories": self.check_core_directories(),
            "core_files": self.check_core_files(),
            "database_integrity": self.check_database_integrity(),
            "settings_validity": self.check_settings_validity(),
            "python_syntax": self.check_python_syntax(),
            "file_hashes": self.check_file_hashes(),
        }

        print("\n" + "=" * 50)
        print("📊 검사 결과 요약")
        print("=" * 50)

        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)

        for check_name, result in results.items():
            status = "✅ 통과" if result else "❌ 실패"
            print(f"  {check_name}: {status}")

        print(f"\n🎯 전체 결과: {success_count}/{total_count} 통과")

        if self.errors:
            print(f"\n❌ 오류 ({len(self.errors)}개):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n⚠️ 경고 ({len(self.warnings)}개):")
            for warning in self.warnings:
                print(f"  - {warning}")

        overall_success = success_count == total_count and not self.errors

        if overall_success:
            print("\n🎉 시스템 무결성 검사 통과!")
        else:
            print("\n💥 시스템 무결성 검사 실패!")

        return {
            "success": overall_success,
            "results": results,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def main():
    """메인 실행 함수"""
    checker = SystemIntegrityChecker()
    result = checker.run_full_check()

    if not result["success"]:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
