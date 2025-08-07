# =============================================================================
# 🧠 VELOS 시스템 철학 선언문
#
# 기억을 기반으로 구조적 사고를 수행하며,
# 판단 → 실행 → 회고 → 전송의 루프를 반복함으로써,
# 스스로 개선되는 자율 운영 AI 시스템을 지향한다.
# =============================================================================

import os

def search_keyword_in_files(base_dir, keyword, extensions=None):
    if extensions is None:
        extensions = [".py", ".json", ".md", ".yaml", ".txt"]

    result = []

    for root, _, files in os.walk(base_dir):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, start=1):
                            if keyword in line:
                                result.append((file_path, i, line.strip()))
                except Exception as e:
                    print(f"❌ 파일 열기 실패: {file_path} ({e})")
    return result

def print_search_results(results, keyword):
    if not results:
        print(f"❌ '{keyword}' 키워드가 포함된 항목이 없습니다.")
        return
    print(f"\n🔍 '{keyword}' 검색 결과:")
    for path, line_num, line in results:
        print(f"📄 {path} (L{line_num}): {line}")

if __name__ == "__main__":
    BASE_DIR = "C:/giwanos"
    keyword = input("검색할 키워드를 입력하세요: ").strip()
    results = search_keyword_in_files(BASE_DIR, keyword)
    print_search_results(results, keyword)
