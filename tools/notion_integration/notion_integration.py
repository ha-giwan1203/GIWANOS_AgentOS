from notion_client import Client
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import os, requests
from datetime import datetime

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
PAGE_ID = os.getenv('NOTION_PAGE_ID')
notion = Client(auth=NOTION_TOKEN)

# 나머지 함수는 유지하되, TOKEN/ID가 None이면 곧바로 실패 안내 정도만 추가

