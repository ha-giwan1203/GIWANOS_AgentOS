# [ACTIVE] VELOS 모니터링 대시보드 - 시스템 모니터링 인터페이스
import os, json, time, re, threading, queue, base64, urllib.parse
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd

st.set_page_config(page_title="VELOS 대시보드", layout="wide")

# ---------- 공통 스타일 ----------
def _inject_base_css():
    st.markdown("""
    <style>
      .role-badge {
        display:inline-block; padding:2px 8px; border-radius:10px;
        font-size:12px; font-weight:600; margin-right:6px;
      }
      .role-user { background:#dbeafe; color:#1e40af; }
      .role-assistant { background:#dcfce7; color:#166534; }
      .role-system { background:#e5e7eb; color:#374151; }
      .chat-item {
        border:1px solid #1f2937; border-radius:10px; padding:10px 12px;
        margin:6px 0; background:#0b1220;
      }
      .log-error { color:#fecaca; }
      .log-warn  { color:#fde68a; }
      .log-info  { color:#bfdbfe; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New", monospace; }
    </style>
    """, unsafe_allow_html=True)

# ---------- 파일 유틸 ----------
def list_files(folder: Path, pattern: str):
    if not folder.exists():
        return []
    return sorted(folder.glob(pattern))

def read_text(path: Path, tail_lines=None):
    if not path.exists():
        return ""
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if tail_lines and tail_lines > 0:
        return "\n".join(txt.splitlines()[-tail_lines:])
    return txt

# ---------- 로그 파싱 ----------
LOG_LINE = re.compile(r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?\s(?P<lvl>INFO|WARNING|ERROR)")

def parse_log_levels(text: str):
    c = {"INFO":0,"WARNING":0,"ERROR":0}
    for m in LOG_LINE.finditer(text):
        c[m.group("lvl")] += 1
    return c

# ---------- 컨텍스트 파싱 ----------
CTX_LINE = re.compile(
    r"^\[(?P<ts>\d{9,})\]\s+\((?P<role>user|system|assistant)\)\s*(?:\[(?P<topic>.*?)\])?\s*(?P<content>.*?)(?:\s*\|\s*tags=(?P<tags>.*))?$"
)

def parse_context_block(block: str):
    rows = []
    for raw in block.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith(("<<", ">>")):
            continue
        m = CTX_LINE.match(raw)
        if not m:
            continue
        ts = int(m.group("ts"))
        try:
            tstr = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            tstr = str(ts)
        rows.append({
            "time": tstr,
            "role": m.group("role"),
            "topic": m.group("topic") or "",
            "content": (m.group("content") or "").strip(),
            "tags": (m.group("tags") or "").strip(),
        })
    return pd.DataFrame(rows)

def load_context_df():
    hc = load_json_safe(LOGS / "hot_context.json")
    block = hc.get("context_block", "")
    return parse_context_block(block)

# ---------- 렌더링 ----------
def _role_badge(role: str):
    cls = "role-user"
    if role == "assistant": cls = "role-assistant"
    elif role == "system": cls = "role-system"
    return f'<span class="role-badge {cls}">{role}</span>'

def render_chat_stream(df, q: str = ""):
    if df.empty:
        st.info("표시할 대화가 없습니다.")
        return
    if q:
        mask = df["content"].str.contains(q, case=False, regex=False) | df["tags"].str.contains(q, case=False, regex=False)
        df = df[mask]
    for _, r in df.iterrows():
        st.markdown(
            f'''
            <div class="chat-item">
              {_role_badge(r["role"])}
              <span class="mono" style="opacity:.7">{r["time"]}</span>
              {'<span class="mono" style="margin-left:8px;opacity:.7">['+r["topic"]+']</span>' if r["topic"] else ''}
              <div style="margin-top:6px;white-space:pre-wrap">{st._escape_markdown(r["content"])}</div>
              {('<div class="mono" style="margin-top:6px;opacity:.6">tags: '+st._escape_markdown(r["tags"])+'</div>') if r["tags"] else ''}
            </div>
            ''',
            unsafe_allow_html=True
        )

def render_log_tail(path: Path, tail_n: int, q: str = ""):
    txt = read_text(path, tail_lines=tail_n)
    if q:
        pattern = re.compile(re.escape(q), re.IGNORECASE)
        def _hl(line: str):
            return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", line)
        txt = "\n".join(_hl(l) for l in txt.splitlines())
    txt = txt.replace(" ERROR ", ' <span class="log-error">ERROR</span> ') \
             .replace(" WARNING ", ' <span class="log-warn">WARNING</span> ') \
             .replace(" INFO ", ' <span class="log-info">INFO</span> ')
    st.markdown(f'<div class="mono" style="font-size:13px; line-height:1.35; white-space:pre-wrap">{txt}</div>', unsafe_allow_html=True)

# ---------- 요약 카드 ----------
def summary_cards(app_log: Path, show_cols=3):
    txt = read_text(app_log, tail_lines=2000)
    lv = parse_log_levels(txt)
    col = st.columns(show_cols)
    with col[0]: st.metric("최근 INFO",   lv["INFO"])
    with col[1]: st.metric("최근 WARNING",lv["WARNING"])
    with col[2]: st.metric("최근 ERROR",  lv["ERROR"])
    if lv["ERROR"] > 0:
        st.error("최근 로그에 ERROR가 감지되었습니다.")


# ============== [NEW] 실시간 대화 뷰 ==============

import json, glob, time, pathlib
from datetime import datetime
import streamlit as st
import pandas as pd

# ============== [NEW] 데이터 정규화 유틸리티 ==============

POSSIBLE_ROLE_KEYS    = ("role", "author", "speaker", "who")
POSSIBLE_TEXT_KEYS    = ("content", "text", "message", "body")
POSSIBLE_TIME_KEYS    = ("ts", "time", "timestamp", "created_at")
POSSIBLE_SESSION_KEYS = ("session", "session_id", "sid")

def _to_dt(v):
    # 숫자(epoch)·문자 모두 허용
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(float(v))
        v = str(v)
        # ISO-like
        return datetime.fromisoformat(v.replace("Z","+00:00"))
    except Exception:
        return None

def normalize_record(raw: dict, src_path: str) -> dict:
    # role
    role = next((raw.get(k) for k in POSSIBLE_ROLE_KEYS if k in raw and raw.get(k)), None)
    if not role:
        # 이벤트/메모리 라인에는 role이 없는 경우가 많음 → 기본값 부여
        t = (raw.get("type") or "").lower()
        if "assistant" in t:
            role = "assistant"
        elif "user" in t:
            role = "user"
        else:
            role = "system"
    role = str(role).lower()

    # content
    content = next((raw.get(k) for k in POSSIBLE_TEXT_KEYS if k in raw and raw.get(k)), None)
    if content is None:
        # 마지막 보루: 사람이 읽을 수 있게 요약
        content = raw.get("summary") or raw.get("event") or json.dumps(raw, ensure_ascii=False)[:2000]

    # timestamp
    ts = next((raw.get(k) for k in POSSIBLE_TIME_KEYS if k in raw and raw.get(k) is not None), None)
    ts = _to_dt(ts) or datetime.now()

    # session id
    session = next((raw.get(k) for k in POSSIBLE_SESSION_KEYS if k in raw and raw.get(k)), None)
    if not session:
        session = Path(src_path).stem  # 파일명으로 대체

    return {
        "role": role,
        "content": content,
        "ts": ts,
        "session": session,
        "_src": src_path,
    }

# 실시간 수집 대상 패턴 (필요시 경로 맞춰 조정)
CHAT_GLOBS = [
    r"C:\giwanos\data\sessions\*.json",      # 세션 대화
    r"C:\giwanos\data\memory\*buffer*.jsonl",# 실시간 버퍼
    r"C:\giwanos\data\memory\tasks_*.jsonl", # 작업 히스토리
    r"C:\giwanos\data\logs\chat_*.jsonl",    # 선택: 채팅 로그가 따로 있을 때
]

def _find_chat_files() -> list[pathlib.Path]:
    files = []
    for pattern in CHAT_GLOBS:
        files += [pathlib.Path(p) for p in glob.glob(pattern)]
    # 최근 것부터
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)

def load_records():
    """완전한 데이터 로딩 시스템 - JSON/JSONL 모두 지원"""
    rows = []
    for pattern in CHAT_GLOBS:
        for p in glob.glob(pattern):
            suffix = Path(p).suffix.lower()
            try:
                if suffix == ".jsonl":
                    with open(p, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            raw = json.loads(line)
                            rows.append(normalize_record(raw, p))
                else:  # .json
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # 세션 파일이 배열/딕셔너리 모두 가능
                    if isinstance(data, list):
                        for raw in data:
                            rows.append(normalize_record(raw, p))
                    elif isinstance(data, dict):
                        # common 형태: {"messages":[...]} 혹은 {"history":[...]}
                        seq = data.get("messages") or data.get("history") or []
                        if isinstance(seq, list) and seq:
                            for raw in seq:
                                rows.append(normalize_record(raw, p))
                        else:  # 모르는 구조 → 한 덩어리라도 normalize
                            rows.append(normalize_record(data, p))
            except Exception as e:
                # 파일 하나가 망가져도 전체는 계속
                rows.append(normalize_record({"type":"parse_error","message":str(e)}, p))

    df = pd.DataFrame(rows)
    # 컬럼 강제 보정 (없어도 에러 안 나게)
    for c in ["role", "content", "ts", "session", "_src"]:
        if c not in df.columns:
            df[c] = ""
    if not df.empty:
        # 정렬 기본: 시간 오름차순
        df = df.sort_values("ts").reset_index(drop=True)
    return df

def _load_messages(files: list[pathlib.Path], since_ts: float | None = None, limit: int = 500):
    """기존 호환성을 위한 래퍼 함수"""
    df = load_records()

    # 필터링 적용
    if since_ts and not df.empty:
        df = df[df["ts"] >= since_ts]

    # 제한 적용
    if len(df) > limit:
        df = df.tail(limit)

    return df

def render_balloon(row):
    mine = row["role"] in ("user","system")  # 왼/오른쪽 기준 원하는 대로
    align = "flex-end" if mine else "flex-start"
    bg = "#0ea5e9" if mine else "#334155"
    txt = str(row["content"]).replace("\n","<br>")
    st.markdown(
        f"""
        <div style="display:flex; justify-content:{align}; margin:4px 0;">
          <div style="max-width:70%; padding:10px 12px; border-radius:12px;
                      background:{bg}; color:white; font-size:14px;">
            <div style="opacity:.8; font-size:12px; margin-bottom:2px;">
                [{row['ts']}] {row['role']}
            </div>
            {txt}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def _chat_bubble(role: str, text: str):
    if role.lower().startswith("user"):
        with st.chat_message("user"):
            st.markdown(text)
    else:
        with st.chat_message("assistant"):
            st.markdown(text)

def page_live():
    st.header("🔴 실시간 대화 모니터")

    # 컨트롤 UI
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        refresh = st.slider("새로고침 주기(초)", 3, 60, 10, 1)
    with col2:
        show_last = st.selectbox("표시 범위", ["최근 100개", "최근 300개", "최근 500개"])
        limit = int(show_last.split()[1][:-1])
    with col3:
        role_filter = st.multiselect("역할 필터", ["user", "assistant"], default=["user","assistant"])
    with col4:
        kw = st.text_input("키워드 포함", value="")

    # 데이터 로딩
    df = load_records()
    if df.empty:
        st.warning("대화 로그를 찾지 못했습니다. `sessions/` 또는 `memory/*jsonl` 경로를 확인하세요.")
        return

    # 역할 필터가 있어도, 컬럼 없으면 죽지 않도록 가드
    if "role" in df.columns and role_filter:
        df = df[df["role"].str.lower().isin([r.lower() for r in role_filter])]

    # 키워드 필터링
    if kw and "content" in df.columns:
        df = df[df["content"].str.contains(kw, case=False, na=False)]

    # 제한 적용
    if len(df) > limit:
        df = df.tail(limit)

    # 상단 요약
    meta = st.container()
    with meta:
        left, mid, right = st.columns([1,2,1])
        with left:
            st.metric("로드된 메시지", len(df))
        with mid:
            st.caption("데이터 소스:  \n" + "\n".join([f"- `{p}`" for p in CHAT_GLOBS[:3]]))
        with right:
            if st.button("새로고침", use_container_width=True):
                st.experimental_rerun()

    st.divider()

    # 메시지 렌더링
    if df.empty:
        st.info("표시할 메시지가 없습니다.")
    else:
        for _, r in df.iterrows():
            render_balloon(r)

    st.divider()
    # 하단 바: 자동 새로고침
    st.caption("자동 새로고침 동작 중…")
    st.experimental_rerun() if st.autorefresh(interval=refresh * 1000, key="live_ref") else None

ROOT = Path(os.getenv("VELOS_ROOT", "C:/giwanos"))
DATA = ROOT / "data"
REPORTS = DATA / "reports" / "auto"
DISPATCH = DATA / "reports" / "_dispatch"
LOGS = DATA / "logs"
SESSION = DATA / "session"
MEMORY = DATA / "memory"


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


def main():
    st.write(":green[boot] 대시보드 초기화…")  # 첫 프레임 강제

    # CSS 스타일 주입
    _inject_base_css()

    # -------- 사이드바: 제어/필터 --------
    st.sidebar.header("🔎 검색 옵션")

    # 기본 경로 표시
    default_paths = [
        str(REPORTS),
        str(LOGS),
        str(MEMORY),
        str(SESSION),
        str(DATA / "snapshots"),
        str(DISPATCH),
    ]

    st.sidebar.markdown("**검색 경로**")
    for p in default_paths:
        st.sidebar.code(p)

    # 실시간 새로고침 옵션
    auto_refresh = st.sidebar.checkbox("🔄 실시간 새로고침 (30초)", value=False)
    if auto_refresh:
        time.sleep(0.1)  # 짧은 지연으로 새로고침 효과

    # -------- 메인 대시보드 --------
    st.title("🛰️ VELOS 모니터 대시보드")

    # 시스템 요약 카드
    app_log = LOGS / "velos_bridge.log"
    if app_log.exists():
        summary_cards(app_log)

    tab_report, tab_dispatch, tab_logs, tab_memory, tab_live = st.tabs(
        ["보고서","디스패처","로그","메모리","실시간"]
    )

    with tab_report:
        st.subheader("📊 자동 보고서")

        # 최근 보고서 파일들
        report_files = list(REPORTS.glob("*.pdf")) + list(REPORTS.glob("*.md"))
        report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if report_files:
            st.success(f"총 {len(report_files)}개의 보고서 파일 발견")

            # 최근 10개 표시
            for i, report_file in enumerate(report_files[:10]):
                with st.expander(f"{report_file.name} ({time.ctime(report_file.stat().st_mtime)})"):
                    if report_file.suffix == '.md':
                        try:
                            content = report_file.read_text(encoding='utf-8')
                            st.text_area("내용", content, height=200, key=f"report_{i}")
                        except Exception as e:
                            st.error(f"파일 읽기 오류: {e}")
                    else:
                        st.info(f"PDF 파일: {report_file.name}")
                        # PDF 다운로드 링크
                        st.markdown(f"[📥 다운로드]({report_file.as_uri()})")
        else:
            st.warning("보고서 파일이 없습니다.")

    with tab_dispatch:
        st.subheader("📋 디스패치 로그")

        # 디스패치 파일들
        dispatch_files = list(DISPATCH.glob("*.json"))
        dispatch_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if dispatch_files:
            st.success(f"총 {len(dispatch_files)}개의 디스패치 파일 발견")

            # 최근 5개 표시
            for i, dispatch_file in enumerate(dispatch_files[:5]):
                with st.expander(f"{dispatch_file.name} ({time.ctime(dispatch_file.stat().st_mtime)})"):
                    try:
                        data = load_json_safe(dispatch_file)
                        st.json(data)

                        # Notion/Slack 링크 표시
                        notion_url = notion_page_url_from_dispatch(data)
                        slack_url = slack_permalink_from_dispatch(data)

                        if notion_url:
                            st.markdown(f"[📝 Notion 페이지]({notion_url})")
                        if slack_url:
                            st.markdown(f"[💬 Slack 메시지]({slack_url})")
                    except Exception as e:
                        st.error(f"파일 읽기 오류: {e}")
        else:
            st.warning("디스패치 파일이 없습니다.")

    with tab_logs:
        st.subheader("📝 시스템 로그")

        # 로그 파일들
        log_files = list(LOGS.glob("*.log")) + list(LOGS.glob("*.txt"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if log_files:
            st.success(f"총 {len(log_files)}개의 로그 파일 발견")

            # 로그 파일 선택
            selected_log = st.selectbox("로그 파일 선택", [f.name for f in log_files])

            if selected_log:
                log_file = next(f for f in log_files if f.name == selected_log)

                # 로그 검색 필터
                log_search = st.text_input("🔍 로그 내용 검색", placeholder="로그에서 검색할 키워드...")

                # 표시할 줄 수
                tail_lines = st.slider("표시할 줄 수", 50, 500, 200, step=50)

                try:
                    # 새로운 렌더링 함수 사용
                    render_log_tail(log_file, tail_lines, log_search)
                except Exception as e:
                    st.error(f"로그 읽기 오류: {e}")
        else:
            st.warning("로그 파일이 없습니다.")

    with tab_memory:
        st.subheader("💾 메모리 상태")

        # 메모리 파일들
        memory_files = list(MEMORY.glob("*.json")) + list(MEMORY.glob("*.jsonl"))
        memory_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if memory_files:
            st.success(f"총 {len(memory_files)}개의 메모리 파일 발견")

            # 메모리 파일 선택
            selected_memory = st.selectbox("메모리 파일 선택", [f.name for f in memory_files])

            if selected_memory:
                memory_file = next(f for f in memory_files if f.name == selected_memory)
                try:
                    if memory_file.suffix == '.json':
                        data = load_json_safe(memory_file)
                        st.json(data)
                    else:  # .jsonl
                        lines = tail_file(memory_file, 50)
                        st.text_area("최근 메모리 항목", "\n".join(lines), height=400)
                except Exception as e:
                    st.error(f"메모리 파일 읽기 오류: {e}")
        else:
            st.warning("메모리 파일이 없습니다.")

    with tab_live:
        page_live()

    # -------- 푸터 --------
    st.markdown("---")
    st.caption(f"VELOS ROOT: {ROOT} • 마지막 갱신: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("렌더링 중 오류 발생")
        st.exception(e)   # 화면에 스택트레이스 표시
        raise
