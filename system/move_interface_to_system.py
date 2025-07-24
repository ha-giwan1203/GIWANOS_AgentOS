
import os
import shutil

BASE_DIR = "C:/giwanos"

# 이동 대상 파일 정의
files_to_move = [
    "move_to_docs.py",
    "move_to_interface.py",
    "move_to_logs.py",
    "move_to_loop_backups.py",
    "move_to_memory.py",
    "move_to_reports.py"
]

def move_files(source_dir, target_dir, files):
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
    source_dir = os.path.join(BASE_DIR, "interface")
    target_dir = os.path.join(BASE_DIR, "system")

    print("📂 'interface' 폴더의 파일을 'system' 폴더로 이동 시작...\n")

    moved_files, errors = move_files(source_dir, target_dir, files_to_move)

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
