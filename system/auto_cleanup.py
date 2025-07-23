import os
import shutil

BASE_DIR = "C:/giwanos"

# 삭제할 확장자 및 폴더 목록
DELETE_EXTENSIONS = ['.pyc', '.tmp', '.log', '.bak', '.driveupload', '.swp']
DELETE_FOLDERS = ['__pycache__', '.tmp.driveupload', '.git_broken_backup', 'logs_backup']

def delete_files_and_folders(base_dir):
    deleted_files = []
    deleted_dirs = []

    for root, dirs, files in os.walk(base_dir):
        # 불필요한 파일 삭제
        for file in files:
            if any(file.endswith(ext) for ext in DELETE_EXTENSIONS):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                deleted_files.append(file_path)

        # 불필요한 폴더 삭제
        for folder in dirs:
            if folder in DELETE_FOLDERS:
                folder_path = os.path.join(root, folder)
                shutil.rmtree(folder_path, ignore_errors=True)
                deleted_dirs.append(folder_path)

    # 삭제된 파일과 폴더 출력
    print("\n🗑️ 삭제된 파일 목록:")
    for file in deleted_files:
        print(f"✅ 파일 삭제: {file}")

    print("\n🗑️ 삭제된 폴더 목록:")
    for folder in deleted_dirs:
        print(f"✅ 폴더 삭제: {folder}")

if __name__ == "__main__":
    delete_files_and_folders(BASE_DIR)
