
import shutil
import os

base_dir = 'C:/giwanos/'

# 실제 현재 파일 위치를 정확히 반영한 최종 파일 이동 목록
final_move_files_list = [
    # 정확한 현재 위치 반영
    ('giwanos_agent', 'judge_agent.py', 'core'),
    ('notifications', 'git_sync.py', 'automation/git_management')
]

# 이동 작업 수행
for current_folder, file_name, target_folder in final_move_files_list:
    src = os.path.join(base_dir, current_folder, file_name)
    dst_dir = os.path.join(base_dir, target_folder)
    dst = os.path.join(dst_dir, file_name)

    os.makedirs(dst_dir, exist_ok=True)

    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"{file_name} 이동 완료 -> {target_folder}")
    else:
        print(f"{file_name} 파일이 존재하지 않습니다 ({src})")
