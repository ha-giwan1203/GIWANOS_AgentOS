# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================

import os
import zipfile
import datetime
import sys
import json
from typing import List, Dict, Any

ROOT = r"C:\giwanos"
SNAPSHOT_DIR = os.path.join(ROOT, "data", "snapshots")
TARGETS = [
    os.path.join(ROOT, "data", "memory"),
    os.path.join(ROOT, "data", "reflections"),
    os.path.join(ROOT, "configs"),
]

def create_snapshot() -> Dict[str, Any]:
    """VELOS 시스템 스냅샷 생성"""
    try:
        # 스냅샷 디렉토리 생성
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)

        # 타임스탬프 생성
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        snap_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{ts}.zip")

        # 파일 통계
        total_files = 0
        total_size = 0
        file_details = []

        # ZIP 파일 생성
        with zipfile.ZipFile(snap_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for target in TARGETS:
                if not os.path.exists(target):
                    continue

                target_name = os.path.basename(target)
                target_files = 0
                target_size = 0

                for root, _, files in os.walk(target):
                    for f in files:
                        full_path = os.path.join(root, f)
                        arcname = os.path.relpath(full_path, ROOT)

                        try:
                            # 파일 크기 확인
                            file_size = os.path.getsize(full_path)

                            # ZIP에 추가
                            zf.write(full_path, arcname)

                            total_files += 1
                            total_size += file_size
                            target_files += 1
                            target_size += file_size

                        except Exception as e:
                            print(f"[WARNING] 파일 추가 실패: {full_path} - {e}")

                file_details.append({
                    "target": target_name,
                    "files": target_files,
                    "size_bytes": target_size
                })

        # 자가 검증
        if not zipfile.is_zipfile(snap_path):
            raise Exception(f"스냅샷 무결성 실패: {snap_path}")

        # 메타데이터 생성
        metadata = {
            "timestamp": ts,
            "created_at": datetime.datetime.now().isoformat(),
            "snapshot_path": snap_path,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "targets": file_details
        }

        # 메타데이터 저장
        metadata_path = snap_path.replace('.zip', '_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "snapshot_path": snap_path,
            "metadata_path": metadata_path,
            "metadata": metadata
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """메인 실행 함수"""
    result = create_snapshot()

    if result["success"]:
        # 결과를 JSON으로만 출력 (다른 출력 없이)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    else:
        print(f"❌ Snapshot creation failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
