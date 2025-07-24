
import os
import shutil

BASE_DIR = "C:/giwanos"

FILE_MOVE_MAP = {
    "system": [
        "apply_giwanos_patch.bat",
        "install_chromadb.bat",
        "install_cohere.bat",
        "install_langchain_community.bat",
        "patch_agents.ps1",
        "register_giwanos_fullloop_task.ps1",
        "restore_prompt.txt",
        "tracked_clean.txt",
        "tracked_files.txt"
    ],
    "reports": [
        "giwanos_log_report.html"
    ],
    "memory": [
        "loop_history.csv",
        "notion_reflection_date_augmented.csv",
        "current_file_list.txt"
    ],
    "run": [
        "giwanos_start.bat",
        "run_dashboard.bat"
    ]
}

def move_files(base_dir, file_move_map):
    moved_files = []
    errors = []

    for target_folder_name, files in file_move_map.items():
        target_folder = os.path.join(base_dir, target_folder_name)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        for file_name in files:
            source_path = os.path.join(base_dir, file_name)
            target_path = os.path.join(target_folder, file_name)

            if not os.path.exists(source_path):
                print(f"[정보] 파일을 찾을 수 없음: {source_path}")
                continue

            try:
                if os.path.exists(target_path):
                    print(f"[경고] 중복 파일 발견: {target_path}, 기존 파일 삭제 후 덮어쓰기 진행")
                    os.remove(target_path)

                shutil.move(source_path, target_path)
                moved_files.append((source_path, target_path))
                print(f"[성공] {source_path} → {target_path}")
            except Exception as e:
                errors.append((source_path, str(e)))
                print(f"[실패] {source_path} 이동 실패: {e}")

    return moved_files, errors

def main():
    print("📂 최상위 폴더 파일을 목적 폴더로 자동 이동 시작...\n")

    moved_files, errors = move_files(BASE_DIR, FILE_MOVE_MAP)

    if moved_files:
        print(f"\n✅ 총 이동된 파일 개수: {len(moved_files)}개\n")
    else:
        print("🎉 이동할 파일이 없습니다.")

    if errors:
        print(f"\n🚫 발생한 오류: {len(errors)}개\n")
        for path, err in errors:
            print(f"❌ {path}: {err}\n")

if __name__ == "__main__":
    main()
