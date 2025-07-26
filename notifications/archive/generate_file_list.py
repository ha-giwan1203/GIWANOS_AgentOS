import os

BASE_DIR = "C:/giwanos"
output_file = os.path.join(BASE_DIR, "current_file_list.txt")

def generate_file_list(base_dir, output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        for root, _, files in os.walk(base_dir):
            for filename in files:
                file_path = os.path.relpath(os.path.join(root, filename), base_dir)
                file.write(file_path.replace("\\", "/") + "\n")

    print(f"✅ 파일 리스트 생성 완료: {output_file}")

if __name__ == "__main__":
    generate_file_list(BASE_DIR, output_file)
