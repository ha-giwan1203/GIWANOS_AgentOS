
import os
import shutil
import glob

BASE_DIR = "C:/giwanos"

FILE_LOCATIONS = {
    'giwanos_agent': ['controller.py', 'judge_agent.py'],
    'interface': ['status_dashboard.py'],
    'system': ['auto_file_mover.py', 'duplicate_file_cleaner.py', 'auto_cleanup.py'],
    'docs': ['*.md'],
    'memory': ['*.json', '*.db', '*.sqlite3'],
    'reports': ['*.pdf'],
    'loop_backups': ['*.zip'],
    'logs': ['*.log']
}

def move_files_safely(base_dir, file_map):
    moved_files = []
    errors = []

    for folder, patterns in file_map.items():
        target_folder = os.path.join(base_dir, folder)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        for pattern in patterns:
            full_pattern = os.path.join(base_dir, '**', pattern)
            for file_path in glob.glob(full_pattern, recursive=True):
                current_path = os.path.abspath(file_path)

                # Skip if current path is already in the target folder
                if os.path.dirname(current_path) == os.path.abspath(target_folder):
                    continue

                new_path = os.path.join(target_folder, os.path.basename(file_path))

                try:
                    if os.path.exists(new_path) and os.path.samefile(current_path, new_path):
                        print(f"[정보] 원본과 대상 경로가 동일 파일입니다. 이동 건너뜀: {current_path}")
                        continue

                    if os.path.exists(new_path):
                        print(f"[경고] 중복 파일 발견: {new_path}, 기존 파일 삭제 후 덮어쓰기 진행")
                        os.remove(new_path)

                    shutil.move(current_path, new_path)
                    moved_files.append((current_path, new_path))
                    print(f"[성공] {current_path} → {new_path}")
                except Exception as e:
                    errors.append((current_path, str(e)))
                    print(f"[실패] {current_path} 이동 실패: {e}")

    return moved_files, errors

def main():
    print("📂 명시적 파일 자동 정리 (안정성 강화) 시작...\n")

    moved_files, errors = move_files_safely(BASE_DIR, FILE_LOCATIONS)

    if moved_files:
        print(f"\n✅ 총 이동된 파일 개수: {len(moved_files)}개\n")
    else:
        print("🎉 이동할 파일이 없습니다. 모든 파일이 이미 올바른 위치에 있습니다.")

    if errors:
        print(f"\n🚫 발생한 오류: {len(errors)}개\n")
        for path, err in errors:
            print(f"❌ {path}: {err}\n")

if __name__ == "__main__":
    main()
