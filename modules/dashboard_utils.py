# [ACTIVE] VELOS 대시보드 유틸리티 - 대시보드 공통 모듈
import os, json, time, re, threading, queue, base64, urllib.parse
from pathlib import Path
from datetime import datetime
import pandas as pd

ROOT = Path(os.getenv("VELOS_ROOT", "C:/giwanos"))
DATA = ROOT / "data"
REPORTS = DATA / "reports" / "auto"
DISPATCH = DATA / "reports" / "_dispatch"
LOGS = DATA / "logs"
SESSION = DATA / "session"
MEMORY = DATA / "memory"


def with_prefix(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = df.copy()
    out.columns = [f"{prefix}.{c}" for c in out.columns]
    return out


def _safe_attach(df: pd.DataFrame, value, prefix: str = "반환") -> pd.DataFrame:
    """
    df에 value를 안전하게 합친다.
    - value가 DataFrame이면 컬럼을 prefix로 붙여 join
    - value가 dict/list이면 json_normalize 후 join
    - 그 외 스칼라면 단일 컬럼으로 할당
    """
    if isinstance(value, pd.DataFrame):
        tmp = with_prefix(value, prefix)
        return df.join(tmp.reset_index(drop=True), how="left")

    if isinstance(value, dict):
        tmp = pd.json_normalize(value)
        tmp = with_prefix(tmp, prefix)
        return df.join(tmp.reset_index(drop=True), how="left")

    if isinstance(value, list) and (len(value) > 0) and isinstance(value[0], (dict, list)):
        tmp = pd.json_normalize(value)
        tmp = with_prefix(tmp, prefix)
        return df.join(tmp.reset_index(drop=True), how="left")

    # 스칼라(문자/숫자)면 단일 컬럼
    df[f"{prefix}"] = value
    return df


def resolve_report_key(key: str):
    # key 예: 20250816_150544
    pdf = next(REPORTS.glob(f"velos_auto_report_{key}_*_ko.pdf"), None) or \
          next(REPORTS.glob(f"velos_auto_report_{key}_ko.pdf"), None)
    dispatch = list(DISPATCH.glob(f"dispatch_{key[:8]}*.json"))
    return {"pdf": pdf, "dispatch": dispatch}


def load_json_safe(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def notion_page_url_from_dispatch(d: dict):
    # dispatch JSON에 page_url 저장되어 있으면 사용
    for k in ("notion", "Notion", "page", "page_url", "NOTION_PAGE_URL"):
        if k in d and isinstance(d[k], str) and d[k].startswith("http"):
            return d[k]
    for k in ("page_url", "notion_page_url"):
        if k in d.get("meta", {}):
            return d["meta"][k]
    return None


def slack_permalink_from_dispatch(d: dict):
    for k in ("slack", "Slack", "SLACK_MESSAGE_URL", "slack_url"):
        v = d.get(k)
        if isinstance(v, str) and v.startswith("http"):
            return v
        if isinstance(v, dict):
            for kk in ("permalink", "url", "message_url"):
                if isinstance(v.get(kk), str) and v[kk].startswith("http"):
                    return v[kk]
    return None


def tail_file(path: Path, n=200):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-n:]


# --- 실시간 tailer (파일 변경 감지) ---
class FileTailStreamer:
    def __init__(self, path: Path, poll_sec: float = 1.0, max_lines=1000):
        self.path = path
        self.poll = poll_sec
        self.max_lines = max_lines
        self._stop = threading.Event()
        self._q = queue.Queue()

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()
        return self

    def stop(self):
        self._stop.set()

    def _run(self):
        last_size = -1
        buf = []
        while not self._stop.is_set():
            try:
                if self.path.exists():
                    now_size = self.path.stat().st_size
                    if now_size != last_size:
                        last_size = now_size
                        buf = tail_file(self.path, self.max_lines)
                        self._q.put(buf)
                time.sleep(self.poll)
            except Exception:
                time.sleep(self.poll)

    def get_latest(self, timeout=0.0):
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None
