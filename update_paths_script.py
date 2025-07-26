
import os

# 변경된 새 경로를 기준으로 파일 경로 업데이트
file_paths = {
    'judge_agent.py': 'core/judge_agent.py',
    'loop_controller.py': 'core/loop_controller.py',
    'git_sync.py': 'automation/git_management/git_sync.py',
    'snapshot_restore.py': 'automation/snapshots/snapshot_restore.py',
    'task_scheduler.py': 'automation/scheduling/task_scheduler.py',
    'send_email.py': 'notifications/send_email.py',
    'send_mobile_notification.py': 'notifications/send_mobile_notification.py',
    'system_health.json': 'data/logs/system_health.json',
    'reflection_20250725.md': 'data/reflections/reflection_20250725.md',
    'weekly_summary_2025W30.md': 'data/summaries/weekly_summary_2025W30.md',
    'evaluation_report.pdf': 'data/reports/evaluation_report.pdf',
    '.env': 'config/.env',
    '.env.example': 'config/.env.example',
    'settings.yaml': 'config/settings.yaml'
}

# 경로 업데이트 결과를 확인 (예시)
for file, path in file_paths.items():
    print(f"{file}의 새 경로는 {path}입니다.")
