import os
import sys
from pathlib import Path

# 프로젝트 루트: C:\giwanos
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# .env 로드 (configs/.env)
try:
    from dotenv import load_dotenv  # python-dotenv
    env_file = ROOT / "configs" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except Exception:
    pass

def get(name: str, default=None):
    return os.getenv(name, default)

# 자주 쓰는 키 alias (필요 없으면 무시 가능)
OPENAI_API_KEY     = get("OPENAI_API_KEY")
SLACK_BOT_TOKEN    = get("SLACK_BOT_TOKEN")
NOTION_TOKEN       = get("NOTION_TOKEN")
PUSHBULLET_API_KEY = get("PUSHBULLET_API_KEY")
EMAIL_PASS         = get("EMAIL_PASS")
SEARCH_API_KEY     = get("SEARCH_API_KEY")


