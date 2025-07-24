
import os
import json
import requests

def load_config():
    with open("notion_config.json", "r", encoding="utf-8") as file:
        return json.load(file)

def upload_to_notion(page_content, config):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {config['token']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    payload = {
        "parent": {"database_id": config['database_id']},
        "properties": {
            config["title_property_name"]: {
                "title": [{"text": {"content": "Weekly Summary"}}]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": page_content}}]}
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    return response

def main():
    summary_file_path = "C:/giwanos/summaries/weekly_summary_2025W30.md"
    
    if not os.path.exists(summary_file_path):
        print("❌ 최신 요약 파일이 없습니다.")
        return

    with open(summary_file_path, "r", encoding="utf-8") as file:
        page_content = file.read()

    config = load_config()
    response = upload_to_notion(page_content, config)

    if response.status_code == 200:
        print("✅ Notion 업로드 성공!")
    else:
        print(f"❌ Notion 업로드 실패: {response.text}")

if __name__ == "__main__":
    main()
