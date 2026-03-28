# [ACTIVE] VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

import json
import zipfile
import os
from pathlib import Path

def backup_orphan_candidates():
    """orphan_candidate 파일들을 백업"""

    # 리포트 로드
    report_path = Path("data/reports/file_usage_report.json")
    if not report_path.exists():
        print("[ERR] 파일 사용성 리포트가 없습니다")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # orphan_candidate 파일들 추출
    orphans = [k for k, v in data['files'].items() if v.get('category') == 'orphan_candidate']
    print(f"[INFO] 총 {len(orphans)}개 orphan_candidate 파일 발견")

    # 백업 디렉토리 생성
    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 백업 파일명
    backup_path = backup_dir / f"orphan_candidates_{Path().cwd().name}_20250817.zip"

    print(f"[INFO] 백업 생성 중: {backup_path}")

    # ZIP 백업 생성
    added_count = 0
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in orphans:
            full_path = Path("C:/giwanos") / file_path
            if full_path.exists():
                try:
                    zf.write(full_path, file_path)
                    added_count += 1
                    print(f"[ADD] {file_path}")
                except Exception as e:
                    print(f"[ERR] {file_path}: {e}")
            else:
                print(f"[MISS] {file_path}")

    print(f"[OK] 백업 완료: {added_count}개 파일 -> {backup_path}")
    return backup_path

if __name__ == "__main__":
    backup_orphan_candidates()
