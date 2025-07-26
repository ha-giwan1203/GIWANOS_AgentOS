
import os
import shutil
import glob

BASE_DIR = "C:/giwanos"
TARGET_FOLDER = os.path.join(BASE_DIR, "logs")
FILE_PATTERN = "*.log"

def move_files_to_logs(base_dir, target_folder, pattern):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    moved_files = []
    errors = []

    for file_path in glob.glob(os.path.join(base_dir, "**", pattern), recursive=True):
        current_path = os.path.abspath(file_path)

        # Skip if the file is already in the target folder
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
    print("📂 'logs' 폴더로 (.log) 파일 자동 정리 시작...\n")

    moved_files, errors = move_files_to_logs(BASE_DIR, TARGET_FOLDER, FILE_PATTERN)

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
