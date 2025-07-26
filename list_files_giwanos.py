
import os
import pandas as pd

# 최상위 폴더 경로
root_dir = 'C:/giwanos'

# 전체 파일 리스트를 담을 리스트
file_list = []

# 폴더 순회하며 파일 경로 수집
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        full_path = os.path.join(subdir, file)
        rel_path = os.path.relpath(subdir, root_dir)
        file_list.append({'현재경로': rel_path, '파일명': file, '이동할경로': ''})

# DataFrame으로 변환
df_files = pd.DataFrame(file_list)

# Excel로 저장
df_files.to_excel('C:/giwanos/file_list.xlsx', index=False)

print('파일 리스트가 성공적으로 저장되었습니다.')
