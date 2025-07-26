
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

def get_path(subpath: str) -> str:
    """루트 기준 하위 경로 생성"""
    return os.path.join(ROOT_DIR, subpath)
