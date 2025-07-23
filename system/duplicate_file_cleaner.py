
import os
import hashlib
from collections import defaultdict

BASE_DIR = "C:/giwanos"

def get_file_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def find_duplicates(base_dir):
    file_dict = defaultdict(list)

    for root, _, files in os.walk(base_dir):
        for file in files:
            filepath = os.path.join(root, file)
            file_hash = get_file_hash(filepath)
            file_dict[(file, file_hash)].append(filepath)

    duplicates = {k: v for k, v in file_dict.items() if len(v) > 1}

    files_to_keep = []
    files_to_delete = []

    for file_info, paths in duplicates.items():
        latest_file = max(paths, key=lambda x: os.path.getmtime(x))
        files_to_keep.append(latest_file)
        files_to_delete.extend([p for p in paths if p != latest_file])

    return files_to_keep, files_to_delete

def main():
    print("🔍 중복 파일 탐색 시작...\n")

    files_to_keep, files_to_delete = find_duplicates(BASE_DIR)

    print(f"📌 발견된 중복 파일 개수: {len(files_to_delete)}개")
    
    if files_to_delete:
        print("\n✅ 유지할 최신 파일:")
        for f in files_to_keep:
            print(f"    유지: {f}")

        print("\n🗑️ 삭제 대상 파일:")
        for f in files_to_delete:
            print(f"    삭제 예정: {f}")

        confirm = input("\n❓ 위의 파일들을 삭제할까요? (y/n): ")
        if confirm.lower() == 'y':
            for f in files_to_delete:
                os.remove(f)
            print("\n✅ 선택된 파일들이 삭제되었습니다.")
        else:
            print("\n❌ 삭제 작업이 취소되었습니다.")
    else:
        print("🎉 중복 파일이 없습니다. 정리할 필요가 없습니다.")

if __name__ == "__main__":
    main()
