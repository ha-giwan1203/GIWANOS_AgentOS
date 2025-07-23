# weekly_summary_generator.py
import os
import glob
import datetime

def summarize_markdown(md_text):
    lines = md_text.strip().split("\n")
    return "\n".join(lines[:5])  # 상위 5줄만 요약

def run():
    folder = "reflections"
    output = []
    files = sorted(glob.glob(os.path.join(folder, "*.md")))

    print(f"🛠 총 {len(files)}개 회고 파일 요약 대상 확인됨")

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            summary = summarize_markdown(f.read())
            output.append(f"### {os.path.basename(file)}\n{summary}\n")
            print(f"✅ 요약됨: {os.path.basename(file)}")

    if not output:
        print("⚠️ 요약할 회고가 없습니다.")
        return

    week = datetime.date.today().isocalendar()[1]
    year = datetime.date.today().year
    out_dir = "summaries"
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, f"weekly_summary_{year}W{week}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 주간 회고 요약\n\n" + "\n".join(output))

    print(f"✅ 주간 요약 저장 완료: {output_path}")

if __name__ == "__main__":
    run()
