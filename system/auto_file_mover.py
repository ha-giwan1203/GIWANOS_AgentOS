
import os
import shutil

BASE_DIR = "C:/giwanos"

TARGET_FOLDERS = {
    '.py': 'system',
    '.md': 'docs',
    '.json': 'memory',
    '.db': 'memory',
    '.sqlite3': 'memory',
    '.pdf': 'reports',
    '.zip': 'loop_backups',
    '.log': 'logs'
}

EXCLUDE_FOLDERS = set(os.path.abspath(os.path.join(BASE_DIR, folder)) for folder in TARGET_FOLDERS.values())

def move_files(base_dir, targets):
    moved_files = []
    planned_moves = []

    for root, dirs, files in os.walk(base_dir, topdown=True):
        dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in EXCLUDE_FOLDERS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in targets:
                target_folder = os.path.abspath(os.path.join(base_dir, targets[ext]))
                current_path = os.path.abspath(os.path.join(root, file))
                new_path = os.path.join(target_folder, file)

                if current_path != new_path:
                    planned_moves.append((current_path, new_path))

    for current_path, new_path in planned_moves:
        if not os.path.exists(current_path):
            print(f"⚠️ 이미 이동되었거나 존재하지 않습니다: {current_path}")
            continue

        target_folder = os.path.dirname(new_path)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        if os.path.exists(new_path):
            print(f"⚠️ 중복된 파일이 존재하여 덮어쓰기: {new_path}")
            os.remove(new_path)

        shutil.move(current_path, new_path)
        moved_files.append((current_path, new_path))

    return moved_files

def main():
    print("📂 파일 자동 이동 시작...\n")

    moved_files = move_files(BASE_DIR, TARGET_FOLDERS)

    if moved_files:
        print(f"\n✅ 총 이동된 파일 개수: {len(moved_files)}개\n")
        for old, new in moved_files:
            print(f"➡️ {old}\n  └ 이동 완료 → {new}\n")
    else:
        print("🎉 이동할 파일이 없습니다. 모든 파일이 이미 올바른 위치에 있습니다.")

if __name__ == "__main__":
    main()
