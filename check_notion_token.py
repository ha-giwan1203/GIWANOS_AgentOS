import os
t = os.getenv("NOTION_TOKEN", "")
print("NOTION_TOKEN length:", len(t))
print("Starts with 'ntn_':", t.startswith("ntn_"))
