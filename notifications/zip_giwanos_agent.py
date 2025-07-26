# C:\giwanos\zip_giwanos_agent.py

import zipfile
import os

def zipdir(path: str, ziph: zipfile.ZipFile):
    # path 폴더의 모든 파일을 zip에 추가
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            # arcname: zip 내에서의 상대 경로
            arcname = os.path.relpath(full_path, os.path.dirname(path))
            ziph.write(full_path, arcname)

if __name__ == "__main__":
    # 1) 에이전트 패키지 폴더 경로
    source_dir = r"C:\giwanos\giwanos_agent"
    # 2) 생성될 ZIP 파일 경로
    output_zip = r"C:\giwanos\giwanos_agent_final.zip"

    # 기존 ZIP 파일이 있으면 삭제
    if os.path.exists(output_zip):
        os.remove(output_zip)

    # ZIP 생성
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipdir(source_dir, zipf)

    print(f"Created ZIP: {output_zip}")
