# [ACTIVE] VELOS 파일 해시 업데이트 시스템 - 파일 무결성 검증 스크립트
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문
"판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

파일 해시 업데이트 스크립트
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path


def update_file_hashes():
    """파일 해시 업데이트"""
    hash_file = Path("configs/security/guard_hashes.json")

    if not hash_file.exists():
        print("❌ 해시 파일이 없습니다")
        return False

    try:
        # 현재 해시 데이터 로드
        with open(hash_file, "r", encoding="utf-8-sig") as f:
            hash_data = json.load(f)

        print("📊 현재 해시 파일 정보:")
        print(f"  업데이트 시간: {hash_data.get('updated_at', 'N/A')}")
        print(f"  파일 수: {len(hash_data.get('files', []))}")

        # 해시 업데이트
        updated_files = []
        for file_info in hash_data.get("files", []):
            file_path = Path(file_info["path"])

            if file_path.exists():
                # 새 해시 계산
                with open(file_path, "rb") as f:
                    content = f.read()
                new_hash = hashlib.sha256(content).hexdigest()

                # 해시 비교
                old_hash = file_info.get("sha256", "")
                if new_hash != old_hash:
                    print(f"🔄 {file_path.name} 해시 업데이트")
                    print(f"  이전: {old_hash[:16]}...")
                    print(f"  새로운: {new_hash[:16]}...")
                    file_info["sha256"] = new_hash
                else:
                    print(f"✅ {file_path.name} 해시 일치")

                updated_files.append(file_info)
            else:
                print(f"⚠️ {file_path.name} 파일 없음 - 제거")

        # 업데이트된 해시 데이터 저장
        hash_data["files"] = updated_files
        hash_data["updated_at"] = datetime.now().isoformat()

        with open(hash_file, "w", encoding="utf-8") as f:
            json.dump(hash_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 해시 파일 업데이트 완료")
        print(f"  업데이트 시간: {hash_data['updated_at']}")
        print(f"  파일 수: {len(updated_files)}")

        return True

    except Exception as e:
        print(f"❌ 해시 업데이트 오류: {e}")
        return False


if __name__ == "__main__":
    update_file_hashes()
