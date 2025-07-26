
import shutil
import os

base_dir = 'C:/giwanos/'

# 실제 파일 위치 반영한 파일 이동 목록
move_files_list = [
    # 핵심 Python 모듈
    ('', 'judge_agent.py', 'core'),
    ('', 'loop_controller.py', 'core'),

    # 자동화 관련 파일
    ('', 'git_sync.py', 'automation/git_management'),
    ('', 'snapshot_restore.py', 'automation/snapshots'),
    ('', 'task_scheduler.py', 'automation/scheduling'),

    # 알림 관련 파일
    ('', 'send_email.py', 'notifications'),
    ('', 'send_mobile_notification.py', 'notifications'),

    # 데이터 및 문서 파일
    ('logs', 'master_loop_execution.log', 'data/logs'),
    ('logs', 'system_health.json', 'data/logs'),
    ('reflections', 'reflection_20250725.md', 'data/reflections'),
    ('summaries', 'weekly_summary_2025W30.md', 'data/summaries'),
    ('reports', 'evaluation_report.pdf', 'data/reports'),

    # 설정 파일
    ('', '.env', 'config'),
    ('', '.env.example', 'config'),
    ('', 'settings.yaml', 'config')
]

# 이동 작업 수행 함수
for current_folder, file_name, target_folder in move_files_list:
    src = os.path.join(base_dir, current_folder, file_name)
    dst_dir = os.path.join(base_dir, target_folder)
    dst = os.path.join(dst_dir, file_name)

    os.makedirs(dst_dir, exist_ok=True)

    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"{file_name} 이동 완료 -> {target_folder}")
    else:
        print(f"{file_name} 파일이 존재하지 않습니다 ({src})")
