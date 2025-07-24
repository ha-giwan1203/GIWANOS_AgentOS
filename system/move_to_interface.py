
import os
import shutil

BASE_DIR = "C:/giwanos"

FILE_MOVES = {
    "status_dashboard.py": "interface"
}

def move_files_to_interface(base_dir, file_moves):
    moved_files = []
    errors = []

    for file_name, target_folder_name in file_moves.items():
        target_folder = os.path.join(base_dir, target_folder_name)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file == file_name:
                    current_path = os.path.abspath(os.path.join(root, file))
                    new_path = os.path.join(target_folder, file)

                    if os.path.abspath(os.path.dirname(current_path)) == os.path.abspath(target_folder):
                        continue

                    try:
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
    print("📂 'interface' 폴더로 정확한 파일 이동 시작...\n")

    moved_files, errors = move_files_to_interface(BASE_DIR, FILE_MOVES)

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
