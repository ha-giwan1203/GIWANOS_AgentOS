
import os
import shutil

BASE_DIR = "C:/giwanos"

files_to_move = [
    "patch_agents.ps1",
    "register_giwanos_fullloop_task.ps1",
    "apply_giwanos_patch.bat",
    "install_chromadb.bat",
    "install_cohere.bat",
    "install_langchain_community.bat"
]

def move_files_to_system(base_dir, files):
    source_dir = base_dir
    target_dir = os.path.join(base_dir, "system")
    moved_files = []
    errors = []

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for file_name in files:
        source_path = os.path.join(source_dir, file_name)
        target_path = os.path.join(target_dir, file_name)

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
    print("📂 최상위 폴더의 누락된 파일을 'system' 폴더로 이동 시작...\n")

    moved_files, errors = move_files_to_system(BASE_DIR, files_to_move)

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
