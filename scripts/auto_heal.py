# [ACTIVE] VELOS 자동 복구 시스템 - 데이터베이스 자동 복구 스크립트
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Path manager imports (Phase 2 standardization)
try:
    from modules.core.path_manager import (
        get_config_path,
        get_data_path,
        get_db_path,
        get_velos_root,
    )
except ImportError:
    # Fallback functions for backward compatibility
    def get_velos_root():
        return "/home/user/webapp"

    def get_data_path(*parts):
        return os.path.join("/home/user/webapp", "data", *parts)

    def get_config_path(*parts):
        return os.path.join("/home/user/webapp", "configs", *parts)

    def get_db_path():
        return "/home/user/webapp/data/memory/velos.db"


"""
VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를
시도한다.

자동 복구 스크립트
VELOS DB의 스키마 문제를 감지하고 자동으로 복구합니다.
"""

import os
import sqlite3
import sys
from pathlib import Path


def _env(key, default=None):
    """환경 변수 로드 (ENV > configs/settings.yaml > 기본값)"""
    import yaml

    # 1. 환경 변수 확인
    value = os.getenv(key)
    if value:
        return value

    # 2. configs/settings.yaml 확인
    try:
        config_path = Path(__file__).parent.parent / "configs" / "settings.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and key in config:
                    return str(config[key])
    except Exception:
        pass

    # 3. 기본값 반환
    return default or "/home/user/webapp"


def check_and_repair_db():
    """DB 스키마 검사 및 복구"""
    db_path = _env(
        "VELOS_DB_PATH",
        (
            get_db_path()
            if "get_db_path" in locals()
            else (
                get_data_path("memory/velos.db")
                if "get_data_path" in locals()
                else "/home/user/webapp/data/memory/velos.db"
            )
        ),
    )

    print(f"VELOS DB 경로: {db_path}")

    if not os.path.exists(db_path):
        print(f"오류: DB 파일이 존재하지 않습니다: {db_path}")
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            print("🔍 DB 스키마 검사 중...")

            # 1. memory 테이블 구조 확인
            cursor = conn.execute("PRAGMA table_info(memory)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            print(f"memory 테이블 컬럼: {list(columns.keys())}")

            expected_columns = ["id", "ts", "role", "insight", "raw", "tags"]
            missing_columns = [col for col in expected_columns if col not in columns]

            if missing_columns:
                print(f"❌ 누락된 컬럼: {missing_columns}")
                return False

            # 2. FTS 테이블 확인
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_fts'"
            )
            fts_exists = cursor.fetchone() is not None

            if not fts_exists:
                print("⚠️ FTS 테이블이 없습니다. 생성 중...")
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE memory_fts USING fts5(
                        insight, raw, content='memory', content_rowid='id',
                        tokenize='unicode61'
                    )
                """
                )
                print("✅ FTS 테이블 생성 완료")

            # 3. FTS 트리거 확인 및 생성
            triggers = ["trg_mem_ai", "trg_mem_ad", "trg_mem_au"]
            for trigger in triggers:
                cursor = conn.execute(
                    f"SELECT name FROM sqlite_master WHERE type='trigger' AND name='{trigger}'"
                )
                if not cursor.fetchone():
                    print(f"⚠️ 트리거 {trigger}가 없습니다. 생성 중...")

                    if trigger == "trg_mem_ai":
                        conn.execute(
                            """
                            CREATE TRIGGER trg_mem_ai AFTER INSERT ON memory BEGIN
                                INSERT INTO memory_fts(rowid, insight, raw)
                                VALUES (new.id, new.insight, new.raw);
                            END
                        """
                        )
                    elif trigger == "trg_mem_ad":
                        conn.execute(
                            """
                            CREATE TRIGGER trg_mem_ad AFTER DELETE ON memory BEGIN
                                INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
                                VALUES('delete', old.id, old.insight, old.raw);
                            END
                        """
                        )
                    elif trigger == "trg_mem_au":
                        conn.execute(
                            """
                            CREATE TRIGGER trg_mem_au AFTER UPDATE ON memory BEGIN
                                INSERT INTO memory_fts(memory_fts, rowid, insight, raw)
                                VALUES('delete', old.id, old.insight, old.raw);
                                INSERT INTO memory_fts(rowid, insight, raw)
                                VALUES (new.id, new.insight, new.raw);
                            END
                        """
                        )

                    print(f"✅ 트리거 {trigger} 생성 완료")

            # 4. 호환성 뷰 확인
            views = ["memory_compat", "memory_roles", "memory_text"]
            for view in views:
                cursor = conn.execute(
                    f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view}'"
                )
                if not cursor.fetchone():
                    print(f"⚠️ 뷰 {view}가 없습니다. 생성 중...")

                    if view == "memory_compat":
                        conn.execute(
                            """
                            CREATE VIEW memory_compat AS
                            SELECT id, ts, role AS "from", role AS source,
                                   insight AS text, raw AS meta
                            FROM memory
                        """
                        )
                    elif view == "memory_roles":
                        conn.execute(
                            """
                            CREATE VIEW memory_roles AS
                            SELECT m.id, m.ts,
                                   COALESCE(
                                       CASE WHEN m.role IN ('user','system','assistant','test')
                                            THEN m.role END, 'unknown'
                                   ) AS role,
                                   m.role AS source, m.insight AS text, m.raw AS meta
                            FROM memory m
                        """
                        )
                    elif view == "memory_text":
                        conn.execute(
                            """
                            CREATE VIEW memory_text AS
                            SELECT id, ts, role, role AS "from", insight AS text_norm, raw, tags
                            FROM memory
                            WHERE insight IS NOT NULL AND insight != ''
                        """
                        )

                    print(f"✅ 뷰 {view} 생성 완료")

            # 5. 인덱스 확인
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            print(f"현재 인덱스: {indexes}")

            # 6. 통계 확인
            cursor = conn.execute("SELECT COUNT(*) FROM memory")
            total_records = cursor.fetchone()[0]
            print(f"총 레코드 수: {total_records}")

            if fts_exists:
                cursor = conn.execute("SELECT COUNT(*) FROM memory_fts")
                fts_records = cursor.fetchone()[0]
                print(f"FTS 인덱스 레코드 수: {fts_records}")

                if fts_records == 0 and total_records > 0:
                    print("⚠️ FTS 인덱스가 비어있습니다. 재구성 중...")
                    # 트리거를 통한 자동 갱신으로 FTS 재구성
                    # memory 테이블의 기존 데이터를 다시 INSERT하여 트리거가 FTS를 갱신하도록 함
                    conn.execute("DELETE FROM memory_fts")
                    conn.execute(
                        """
                        INSERT INTO memory(ts, role, insight, raw, tags)
                        SELECT ts, role, insight, raw, tags FROM memory
                    """
                    )
                    print("✅ FTS 인덱스 재구성 완료 (트리거를 통한 자동 갱신)")

            conn.commit()
            print("✅ DB 검사 및 복구 완료")
            return True

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


if __name__ == "__main__":
    print("VELOS DB 자동 복구 시작...")
    success = check_and_repair_db()

    if success:
        print("✅ 자동 복구 완료")
    else:
        print("❌ 자동 복구 실패")
        sys.exit(1)
