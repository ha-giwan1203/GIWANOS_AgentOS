import os
import shutil

def clean_driveupload_folder(folder_path='.tmp.driveupload'):
    if not os.path.exists(folder_path):
        print(f"폴더가 존재하지 않습니다: {folder_path}")
        return

    deleted = 0
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                deleted += 1
        except Exception as e:
            print(f"삭제 실패: {file_path} - {e}")

    print(f"삭제된 파일 수: {deleted}")

if __name__ == "__main__":
    clean_driveupload_folder()
