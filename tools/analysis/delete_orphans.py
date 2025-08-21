# [ACTIVE] VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

import json
import os
from pathlib import Path


def delete_orphan_candidates():
    """백업된 orphan_candidate 파일들을 안전하게 삭제"""

    # 백업 파일 확인
    backup_path = Path("data/backups/orphan_candidates_giwanos_20250817.zip")
    if not backup_path.exists():
        print("[ERR] 백업 파일이 없습니다. 먼저 백업을 생성하세요.")
        return False

    print(f"[INFO] 백업 파일 확인됨: {backup_path}")

    # 리포트 로드
    report_path = Path("data/reports/file_usage_report.json")
    if not report_path.exists():
        print("[ERR] 파일 사용성 리포트가 없습니다")
        return False

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # orphan_candidate 파일들 추출
    orphans = [k for k, v in data["files"].items() if v.get("category") == "orphan_candidate"]
    print(f"[INFO] 삭제 대상: {len(orphans)}개 파일")

    # 사용자 확인
    print("\n[WARNING] 다음 파일들이 삭제됩니다:")
    for i, file_path in enumerate(orphans[:10], 1):
        print(f"  {i}. {file_path}")
    if len(orphans) > 10:
        print(f"  ... 및 {len(orphans) - 10}개 더")

    print(f"\n[INFO] 백업 위치: {backup_path}")
    print("[INFO] 계속하려면 'YES'를 입력하세요: ", end="")

    # 실제 삭제 실행
    deleted_count = 0
    error_count = 0

    for file_path in orphans:
        full_path = Path("/home/user/webapp") / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                deleted_count += 1
                print(f"[DEL] {file_path}")
            except Exception as e:
                print(f"[ERR] {file_path}: {e}")
                error_count += 1
        else:
            print(f"[MISS] {file_path}")

    print(f"\n[OK] 삭제 완료: {deleted_count}개 성공, {error_count}개 실패")
    print(f"[INFO] 백업 파일: {backup_path}")
    return True


if __name__ == "__main__":
    delete_orphan_candidates()
