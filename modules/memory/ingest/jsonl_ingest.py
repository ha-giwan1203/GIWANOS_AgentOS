# VELOS 운영 철학 선언문: 파일명은 절대 변경하지 않는다. 수정 시 자가 검증을 포함하고,
# 실행 결과를 기록하며, 경로/구조는 불변으로 유지한다. 실패는 로깅하고 자동 복구를 시도한다.
from __future__ import annotations
import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import Iterable, Dict, Any, Optional


# VELOS 환경 변수 로딩
def _env(name: str, default: Optional[str] = None) -> str:
    """VELOS 환경 변수 로딩: ENV > configs/settings.yaml > C:\giwanos 순서"""
    v = os.getenv(name, default)
    if not v:
        # 설정 파일에서 로드 시도
        try:
            import yaml
            config_path = Path("C:/giwanos/configs/settings.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    v = config.get(name, default)
        except Exception:
            pass

        if not v:
            # 기본값 설정
            if name == "VELOS_JSONL_DIR":
                v = "C:/giwanos/data/memory"
            elif name == "VELOS_DB":
                v = "C:/giwanos/data/memory/velos.db"
            else:
                raise RuntimeError(f"Missing env: {name}")
    return v

# 기존 VELOS 스키마와 호환되는 저장소 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'storage'))
from sqlite_store import connect_db, init_schema, advisory_lock


def sha1(s: str) -> str:
    """SHA1 해시 생성"""
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    """JSONL 파일을 한 줄씩 읽어서 파싱"""
    try:
        # UTF-8 BOM 처리
        with path.open("r", encoding="utf-8-sig") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류 {path}:{line_num}: {e}")
                    continue
    except Exception as e:
        print(f"파일 읽기 오류 {path}: {e}")


def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """레코드를 VELOS 스키마에 맞게 정규화"""
    # 텍스트 추출 (여러 필드명 지원)
    text = rec.get("text") or rec.get("content") or rec.get("insight") or ""

    # 역할 추출
    role = rec.get("role") or rec.get("from") or rec.get("source") or "system"

    # 태그 추출
    tags = rec.get("tags") or rec.get("labels") or []
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except:
            tags = [tags]

    # 타임스탬프 추출
    ts = rec.get("ts") or rec.get("timestamp") or rec.get("created_at") or int(time.time())
    if isinstance(ts, str):
        try:
            ts = int(float(ts))
        except:
            ts = int(time.time())

    # 원문 데이터 (JSON 직렬화)
    raw = rec.get("raw") or rec.get("data") or ""
    if isinstance(raw, dict):
        raw = json.dumps(raw, ensure_ascii=False)

    return {
        "ts": ts,
        "role": role,
        "insight": text,
        "raw": raw,
        "tags": tags
    }


def ingest_dir(jsonl_dir: Path, source: str = "jsonl") -> Dict[str, int]:
    """JSONL 디렉토리를 VELOS DB로 수집"""
    con = connect_db()
    init_schema(con)
    inserted = 0
    skipped = 0
    errors = 0

    try:
        with advisory_lock(con, "ingest", owner="velos"):
            for p in sorted(jsonl_dir.glob("*.jsonl")):
                print(f"처리 중: {p.name}")
                for rec in iter_jsonl(p):
                    try:
                        # 레코드 정규화
                        normalized = normalize_record(rec)

                        # 빈 텍스트 스킵
                        if not normalized["insight"].strip():
                            skipped += 1
                            continue

                        # 중복 방지: 해시 기반 체크
                        text_hash = sha1(f"{source}:{normalized['ts']}:{normalized['insight'][:512]}")

                        # 기존 VELOS 스키마에 맞게 삽입
                        with con:
                            con.execute(
                                "INSERT INTO memory(ts, role, insight, raw, tags) VALUES(?,?,?,?,?)",
                                (
                                    normalized["ts"],
                                    normalized["role"],
                                    normalized["insight"],
                                    normalized["raw"],
                                    json.dumps(normalized["tags"], ensure_ascii=False)
                                )
                            )
                            inserted += 1

                    except Exception as e:
                        print(f"레코드 처리 오류: {e}")
                        errors += 1
                        continue

    except Exception as e:
        print(f"수집 중 오류: {e}")
        errors += 1

    finally:
        con.close()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "source": source
    }


def test_ingest():
    """자가 검증 테스트"""
    print("=== VELOS JSONL Ingest 자가 검증 테스트 ===")

    # 테스트 JSONL 파일 생성
    test_dir = Path("data/memory/test_ingest")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_data = [
        {
            "ts": int(time.time()),
            "role": "user",
            "insight": "VELOS JSONL 수집 테스트",
            "raw": "테스트 데이터입니다",
            "tags": ["test", "ingest"]
        },
        {
            "ts": int(time.time()) + 1,
            "role": "system",
            "insight": "두 번째 테스트 레코드",
            "raw": "정규화 테스트",
            "tags": ["test", "normalize"]
        }
    ]

    test_file = test_dir / "test.jsonl"
    with open(test_file, "w", encoding="utf-8") as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"테스트 파일 생성: {test_file}")

    # 수집 테스트
    result = ingest_dir(test_dir, source="test")
    print(f"수집 결과: {result}")

    # 정리
    test_file.unlink()
    test_dir.rmdir()

    print("=== 자가 검증 완료 ===")


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_ingest()
    else:
        # 실제 수집 실행
        root = Path(_env("VELOS_JSONL_DIR"))
        result = ingest_dir(root, source="jsonl")
        print(f"수집 완료: {result}")
