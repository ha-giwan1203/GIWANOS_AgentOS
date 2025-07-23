import os
import subprocess
import shutil


def generate_commit_message(filename):
    if "weekly_summary" in filename:
        return f"📅 주간 요약 보고서 업데이트: {filename}"
    elif "loop_reflection_log.md" in filename:
        return f"📝 회고 마크다운 자동 생성됨: {filename}"
    elif "loop_reflection_log.pdf" in filename:
        return f"📄 회고 PDF 보고서 저장됨: {filename}"
    elif "evaluation_aggregated_log.jsonl" in filename:
        return f"📊 평가 점수 기록됨 (점수: 4.5)"
    elif "upload_final_runner.py" in filename:
        return "🔗 회고 결과 Notion 전송 완료"
    elif "run_giwanos_master_loop.py" in filename:
        return "🔁 GIWANOS 전체 루프 실행 결과 저장"
    elif "release_all_github.py" in filename:
        return "🚀 시스템 릴리즈 태그 생성됨: v1.3.0"
    else:
        return "☁️ GitHub 자동 백업 실행"

def cleanup_tmp_driveupload():
    folder_path = ".tmp.driveupload"
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            print("[정리 완료] .tmp.driveupload 폴더 삭제 완료")
        except Exception as e:
            print(f"[정리 실패] {e}")

def sync_to_github():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "자동 백업: 최신 상태 동기화"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[✅] GitHub 동기화 완료")
    except subprocess.CalledProcessError as e:
        print(f"[❌] Git 명령 실패: {e}")
    except Exception as e:
        print(f"[❌] 기타 오류: {e}")

if __name__ == "__main__":
    print("[시작] .tmp.driveupload 정리 및 GitHub 자동 동기화")
    cleanup_tmp_driveupload()
    sync_to_github()
