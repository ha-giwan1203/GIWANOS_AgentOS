import pathlib

from dotenv import find_dotenv, load_dotenv

CONFIG_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = CONFIG_DIR.parent

# 루트 또는 configs 폴더 등에서 .env 자동 탐색
load_dotenv(find_dotenv(), override=True)
