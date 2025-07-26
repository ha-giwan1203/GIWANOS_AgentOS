import os
import shutil

# 이동 기준 매핑 (파일명 패턴 일부 → 대상 폴더)
rules = {
    "memory_": "memory",
    "generate_reflection": "reflection",
    "weekly_summary": "reflection",
    "giwanos.reflection.judge_agent": "reflection",
    "send_reflection": "reporting",
    "notion_upload": "reporting",
    "giwanos.reporting.agent_logger": "reporting",
    "system_integrity": "system",
    "check_giwanos_scheduler": "system",
    "giwanos.interface.streamlit_summary_dashboard": "interface",
    "zip_giwanos_agent": "system",
    "upload_final_runner": "reporting"
}

def move_files(base_dir="."):
    for filename in os.listdir(base_dir):
        if not filename.endswith(".py"):
            continue
        for key, folder in rules.items():
            if key in filename:
                src = os.path.join(base_dir, filename)
                dst_dir = os.path.join(base_dir, folder)
                dst = os.path.join(dst_dir, filename)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                print(f"📦 {filename} → {folder}/")
                shutil.move(src, dst)
                break

if __name__ == "__main__":
    move_files()
