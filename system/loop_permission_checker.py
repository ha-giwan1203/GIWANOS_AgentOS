import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json

def has_permission(user, action):
    with open("loop_user_accounts.json", "r", encoding="utf-8") as f:
        accounts = json.load(f)
    user_info = accounts.get(user)
    if not user_info:
        return False
    return action in user_info.get("permissions", [])

if __name__ == "__main__":
    user = "assistant1"
    action = "retire"
    if has_permission(user, action):
        print(f"✅ {user} → '{action}' 권한 있음")
    else:
        print(f"⛔ {user} → '{action}' 권한 없음")
