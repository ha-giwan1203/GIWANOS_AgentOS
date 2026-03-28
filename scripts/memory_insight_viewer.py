# [ACTIVE] VELOS 메모리 인사이트 뷰어 - 메모리 데이터 시각화 시스템
# ---------------- Memory Insight Viewer (고도화) ----------------
# 요구 라이브러리: streamlit, python-dateutil (선택), dotenv(선택)
# pip install python-dateutil python-dotenv streamlit

import os
import json
import csv
import sqlite3
import io
import re
from pathlib import Path
from datetime import datetime, timedelta

try:
    from dateutil.parser import parse as parse_dt
except Exception:
    parse_dt = None

import streamlit as st

# .env 선택 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

VELOS_ROOT = Path(os.getenv("VELOS_ROOT", r"C:\giwanos"))
MEM_DIR = Path(os.getenv("VELOS_MEM_DIR", str(VELOS_ROOT / "data" / "memory")))
MEM_JSONL = MEM_DIR / "learning_memory.jsonl"
MEM_SQLITE = MEM_DIR / "velos.db"
SESS_DIR = VELOS_ROOT / "data" / "sessions"
REFL_DIR = VELOS_ROOT / "data" / "reflections"


def _coerce_ts(s: str) -> datetime | None:
    if not s:
        return None
    if parse_dt:
        try:
            return parse_dt(s)
        except Exception:
            pass
    # 대강 YYYY-MM-DD HH:MM:SS 또는 ISO
    try:
        s = s.replace("T", " ").split(".")[0]
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def read_jsonl_tail(path: Path, limit: int = 5000) -> list[dict]:
    """JSONL의 마지막 N라인을 읽어 dict 리스트로 반환"""
    if not path.exists():
        return []
    # 메모리 폭주 방지: 마지막 limit라인만 읽기
    # 파일이 매우 클 수 있으니 두 번 패스 피한다
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    chunk = lines[-limit:]
    out = []
    for ln in chunk:
        try:
            obj = json.loads(ln)
            # 필드 정규화
            obj.setdefault("ts", obj.get("timestamp") or obj.get("time") or "")
            obj.setdefault("from", obj.get("speaker") or obj.get("role") or obj.get("source") or "")
            obj.setdefault("insight", obj.get("content") or obj.get("message") or obj.get("text") or "")
            # 태그 타입 보정
            tags = obj.get("tags")
            if isinstance(tags, str):
                obj["tags"] = [t.strip() for t in re.split(r"[;,]", tags) if t.strip()]
            elif tags is None:
                obj["tags"] = []
            out.append(obj)
        except Exception:
            # 망가진 라인은 조용히 무시
            continue
    return out


def read_sqlite_recent(db: Path, limit: int = 1000) -> list[dict]:
    if not db.exists():
        return []
    try:
        con = sqlite3.connect(str(db))
        cur = con.cursor()
        # 스키마가 프로젝트마다 다를 수 있으니 방어적으로 필드 매핑
        # 가능한 컬럼 후보: ts|timestamp, from|speaker|role, insight|content|text
        cols = None
        # 정보 스키마 탐색
        cur.execute("PRAGMA table_info(memory);")
        colnames = [r[1].lower() for r in cur.fetchall()]
        # 칼럼 매핑
        c_ts = "ts" if "ts" in colnames else ("timestamp" if "timestamp" in colnames else None)
        c_from = "from" if "from" in colnames else ("speaker" if "speaker" in colnames else ("role" if "role" in colnames else None))
        c_text = "insight" if "insight" in colnames else ("content" if "content" in colnames else ("text" if "text" in colnames else None))
        if not all([c_ts, c_from, c_text]):
            # 스키마 다르면 포기
            con.close()
            return []
        q = f'SELECT {c_ts}, {c_from}, {c_text} FROM memory ORDER BY {c_ts} DESC LIMIT ?'
        cur.execute(q, (limit,))
        rows = [{"ts": r[0], "from": r[1], "insight": r[2]} for r in cur.fetchall()]
        con.close()
        return rows
    except Exception:
        return []


def filter_rows(rows: list[dict], speaker: str, tags: list[str], q: str, start: datetime | None, end: datetime | None) -> list[dict]:
    out = []
    pat = re.compile(re.escape(q), re.I) if q else None
    tagset = set([t.strip().lower() for t in tags if t.strip()])
    for r in rows:
        ts = _coerce_ts(r.get("ts", ""))
        if start and ts and ts < start:
            continue
        if end and ts and ts > end:
            continue
        if speaker and (r.get("from", "").lower() != speaker.lower()):
            continue
        if tagset:
            row_tags = {t.lower() for t in (r.get("tags") or [])}
            if not row_tags.intersection(tagset):
                continue
        if pat:
            blob = " ".join([
                r.get("insight", ""), r.get("from", ""),
                " ".join(r.get("tags") or [])
            ])
            if not pat.search(blob):
                continue
        out.append(r)
    return out


def paginate(rows: list[dict], page: int, page_size: int) -> list[dict]:
    s = max(0, (page - 1) * page_size)
    e = s + page_size
    return rows[s:e]


def export_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ts", "from", "insight", "tags"])
    for r in rows:
        w.writerow([r.get("ts", ""), r.get("from", ""), r.get("insight", ""), ";".join(r.get("tags") or [])])
    return buf.getvalue().encode("utf-8-sig")


# ------------- UI -------------
st.set_page_config(page_title="Memory Insight Viewer", layout="wide")
st.header("🧠 Memory Insight Viewer (실시간 대화·학습 로그)")

src_tab, = st.tabs(["실시간 로그"])

with src_tab:
    # 소스 선택
    st.markdown("#### 데이터 소스")
    source = st.radio("읽기 대상", ["JSONL(권장)", "SQLite"], horizontal=True, label_visibility="collapsed")

    # 컨트롤 패널
    st.markdown("#### 필터")
    cols = st.columns([1, 1, 2, 2, 1, 1])
    with cols[0]:
        speaker = st.selectbox("발화자", ["", "user", "assistant", "system"])
    with cols[1]:
        last_minutes = st.selectbox("최근", ["", "5분", "15분", "1시간", "6시간", "24시간", "7일"])
    with cols[2]:
        start_str = st.text_input("시작(YYYY-MM-DD HH:MM:SS)", value="")
    with cols[3]:
        end_str = st.text_input("종료(YYYY-MM-DD HH:MM:SS)", value="")
    with cols[4]:
        tag_str = st.text_input("태그(쉼표 , 구분)", value="")
    with cols[5]:
        q = st.text_input("키워드", value="")

    # 자동 새로고침
    auto = st.toggle("자동 새로고침(5초)", value=False)
    if auto:
        st.autorefresh(interval=5000, key="mem_auto_refresh")

    # 페이지네이션
    pcol = st.columns([1, 1, 2, 2, 1, 1, 1])
    with pcol[0]:
        page_size = st.selectbox("페이지 크기", [25, 50, 100, 200], index=1)
    with pcol[1]:
        page = st.number_input("페이지", min_value=1, value=1, step=1)

    # 링크 패널
    st.markdown("#### 경로")
    cols2 = st.columns(3)
    with cols2[0]:
        st.write(f"JSONL: `{MEM_JSONL}`")
        st.write(f"SQLite: `{MEM_SQLITE}`")
    with cols2[1]:
        last_ref = None
        if REFL_DIR.exists():
            last = sorted(REFL_DIR.glob("reflection_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            last_ref = last[0] if last else None
        st.write(f"Reflections: `{last_ref or '(없음)'}`")
    with cols2[2]:
        last_sess = None
        if SESS_DIR.exists():
            last = sorted(SESS_DIR.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            last_sess = last[0] if last else None
        st.write(f"Session: `{last_sess or '(없음)'}`")

    # 데이터 로드
    if source.startswith("JSONL"):
        rows = read_jsonl_tail(MEM_JSONL, limit=5000)
    else:
        rows = read_sqlite_recent(MEM_SQLITE, limit=2000)

    # 시간 필터 구문 처리
    start = _coerce_ts(start_str) if start_str else None
    end = _coerce_ts(end_str) if end_str else None
    if last_minutes:
        now = datetime.now()
        span = {
            "5분": 5, "15분": 15, "1시간": 60, "6시간": 360, "24시간": 1440, "7일": 10080
        }[last_minutes]
        start = now - timedelta(minutes=span)
        end = now

    # 태그 파싱
    tags = [t.strip() for t in tag_str.split(",")] if tag_str.strip() else []

    # 필터 적용
    filtered = filter_rows(rows, speaker=speaker, tags=tags, q=q, start=start, end=end)

    # 페이지네이션
    total = len(filtered)
    page_max = max(1, (total + page_size - 1) // page_size)
    if page > page_max:
        page = page_max
    view = paginate(filtered, page=page, page_size=page_size)

    # 액션 버튼들
    cta = st.columns([1, 1, 1, 3])
    with cta[0]:
        st.metric("총 레코드", total)
    with cta[1]:
        if st.button("CSV 내보내기"):
            data = export_csv(filtered)
            st.download_button("CSV 다운로드", data=data, file_name="velos_memory_export.csv", mime="text/csv", use_container_width=True)
    with cta[2]:
        redact = st.toggle("민감정보 가리기(숫자/이메일/토큰 패턴)", value=False)

    # 렌더
    st.divider()
    for r in view:
        ts = r.get("ts", "")
        sp = r.get("from", "")
        text = r.get("insight", "")
        tags_show = ", ".join(r.get("tags") or [])

        if redact:
            # 매우 단순한 마스킹(운영중 과도한 노이즈 방지)
            text = re.sub(r"[A-Za-z0-9]{24,}", "[SECRET]", text)  # 긴 토큰류
            text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
            text = re.sub(r"\b\d{6,}\b", "[NUM]", text)

        st.markdown(f"**{sp or '?'}** · `{ts or '?'}`  \n{text}")
        if tags_show:
            st.caption(f"🏷 {tags_show}")
        st.markdown("---")

    # 바닥 정보
    st.caption(f"페이지 {page}/{page_max} · 표시 {len(view)}/{total} · 소스: {source}")
