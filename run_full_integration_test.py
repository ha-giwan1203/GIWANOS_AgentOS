import subprocess
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))

def run_script(script_path):
    print(f'실행 중: {script_path}')
    result = subprocess.run(['python', script_path], capture_output=True, text=True)
    if result.returncode == 0:
        print(f'✅ 성공: {script_path}\n{result.stdout}')
    else:
        print(f'❌ 실패: {script_path}\n{result.stderr}')

scripts_to_run = [
    'notion_integration/upload_notion_result.py',
    'system/git_sync.py',
    'system/send_evaluation_report.py',
    'advanced_modules/advanced_rag.py',
    'advanced_modules/advanced_vectordb.py'
]

if __name__ == "__main__":
    for script in scripts_to_run:
        full_path = os.path.join(base_dir, script)
        run_script(full_path)

    print("\n🎉 모든 연동 테스트가 완료되었습니다.")