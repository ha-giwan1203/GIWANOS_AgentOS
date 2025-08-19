# [ACTIVE] VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.
# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings("ignore", module="streamlit")
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
import io
import zipfile
import time
import json
import re
import webbrowser
from pathlib import Path
import streamlit as st
import pandas as pd

# VELOS 운영 원칙: interface/* 임포트는 절대 실패하지 않아야 함
def _ensure_velos_path():
    """VELOS_ROOT 환경변수 또는 기본 경로를 sys.path에 추가"""
    velos_root = os.environ.get('VELOS_ROOT')
    if velos_root and os.path.isdir(velos_root):
        if velos_root not in sys.path:
            sys.path.insert(0, velos_root)
            print(f"[velos_dashboard] VELOS_ROOT 추가됨: {velos_root}")
    else:
        # 기본 fallback 경로
        fallback_path = r"C:\giwanos"
        if os.path.isdir(fallback_path) and fallback_path not in sys.path:
            sys.path.insert(0, fallback_path)
            print(f"[velos_dashboard] fallback 경로 추가됨: {fallback_path}")

# 모듈 로드 시 자동으로 경로 보장
_ensure_velos_path()

# 내부 모듈 (선택적 로드)
try:
    from modules.logs.indexer import load_conversations, load_system_metrics
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    # 폴백 함수들
    def load_conversations(days=7, limit=1000, role=None, query=""):
        return pd.DataFrame()
    def load_system_metrics():
        return {"mem": "N/A", "cpu": "N/A", "sessions": "N/A"}

try:
    from modules.utils.pii import scrub_text
    PII_AVAILABLE = True
except ImportError:
    PII_AVAILABLE = False
    def scrub_text(text):
        return text

try:
    from modules.tags.rules import auto_tags
    TAGS_AVAILABLE = True
except ImportError:
    TAGS_AVAILABLE = False
    def auto_tags(text):
        return []

try:
    from modules.vectors.search import embed_search
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    def embed_search(query, topk=10, days=7):
        return [{"content": "벡터 검색 모듈을 사용할 수 없습니다.", "score": 0.0}]

# 경로 설정 - 환경변수 우선, fallback 경로 사용
velos_root = os.environ.get('VELOS_ROOT', r"C:\giwanos")
ROOT = Path(velos_root)
DATA = ROOT / "data"
MEM = DATA / "memory"
LOGS = DATA / "logs"

st.set_page_config(page_title="VELOS 한국어 대시보드", layout="wide")

# -------- 사이드: 제어/필터 저장 --------
st.sidebar.header("🔎 검색 옵션")

# 모듈 상태 표시
if not MODULES_AVAILABLE:
    st.sidebar.warning("⚠️ 내부 모듈을 로드할 수 없습니다.")

default_paths = [
    str(DATA / "reports/auto"),
    str(DATA / "logs"),
    str(DATA / "memory"),
    str(DATA / "sessions"),
    str(DATA / "snapshots"),
    str(DATA / "dispatch/_dispatch"),
]

st.sidebar.markdown("**검색 경로**")
for p in default_paths:
    st.sidebar.code(p)

FILTER_DB = ROOT / "scripts/dispatch_keys.json"
if FILTER_DB.exists():
    presets = json.loads(FILTER_DB.read_text("utf-8"))
else:
    presets = [
        {"name": "최근오류(24h)", "q": "ERROR|Exception|Traceback", "role": "전체", "days": 1, "limit": 1000},
        {"name": "사용자요청(7d)", "q": "", "role": "user", "days": 7, "limit": 1000},
    ]

preset_name = st.sidebar.selectbox("저장된 필터", [p["name"] for p in presets])
col_p1, col_p2 = st.sidebar.columns(2)
if col_p1.button("불러오기", use_container_width=True):
    st.session_state["_active_preset"] = next(p for p in presets if p["name"] == preset_name)
if col_p2.button("저장/덮어쓰기", use_container_width=True):
    cur = st.session_state.get("_active_preset")
    if cur:
        for p in presets:
            if p["name"] == cur["name"]:
                p.update(cur)
                break
        FILTER_DB.write_text(json.dumps(presets, ensure_ascii=False, indent=2), "utf-8")
        st.success("필터 저장됨")

# -------- 상단: 질의 영역 --------
st.title("🛰️ VELOS 한국어 대시보드")

tab1, tab2, tab3, tab4 = st.tabs(["대화 탐색(리스트)", "스레드 뷰", "의미 검색", "시스템/리포트"])

with tab1:
    # 쿼리 입력
    q = st.text_input("키워드(정규식 허용)", value=st.session_state.get("q", ""))
    role = st.selectbox("발화자", ["전체", "user", "assistant", "system"])
    days = st.slider("기간(일)", 1, 90, 7)
    limit = st.slider("표시 개수", 100, 5000, 1000, step=100)
    page_size = st.selectbox("페이지 크기", [50, 100, 200, 500], index=1)
    highlight = st.checkbox("키워드 하이라이트", value=True)
    pii_mask = st.checkbox("민감정보 마스킹(PII)", value=True, disabled=not PII_AVAILABLE)
    auto_refresh = st.checkbox("자동 새로고침(30s)", value=False)

    if auto_refresh:
        st.experimental_rerun() if st.session_state.get("_tick", 0) % 60 == 0 else None
        st.session_state["_tick"] = st.session_state.get("_tick", 0) + 30
        time.sleep(0.5)

    # 프리셋 적용
    if "_active_preset" in st.session_state and st.button("프리셋 적용"):
        ap = st.session_state["_active_preset"]
        q, role, days, limit = ap["q"], ap["role"], ap["days"], ap["limit"]

    # 데이터 적재(캐시)
    df = load_conversations(days=days, limit=limit, role=None if role == "전체" else role, query=q)

    if not df.empty:
        if pii_mask and PII_AVAILABLE:
            df["content"] = df["content"].map(scrub_text)

        if TAGS_AVAILABLE:
            df["tags"] = df["content"].map(lambda x: ", ".join(auto_tags(x)))
        else:
            df["tags"] = ""

        st.success(f"총 {len(df):,}행 로드됨")

        # 페이지네이션
        page = st.number_input("페이지", min_value=1, value=1)
        start, end = (page - 1) * page_size, (page) * page_size
        sdf = df.iloc[start:end].copy()

        # 하이라이트
        if highlight and q:
            pattern = re.compile(q, re.I)
            sdf["content"] = sdf["content"].apply(
                lambda t: pattern.sub(lambda m: f"**:red[{m.group(0)}]**", t)
            )

        # 원본열기 링크
        def open_buttons(row):
            f = row.get("source_path") or ""
            btns = []
            if f and Path(f).exists():
                btns.append(f"[파일열기]({Path(f).as_uri()})")
                btns.append(f"[폴더열기]({Path(f).parent.as_uri()})")
            return " ".join(btns)

        sdf["원본"] = sdf.apply(open_buttons, axis=1)

        st.dataframe(sdf[["time", "role", "session", "content", "tags", "원본"]],
                    use_container_width=True, height=600)

        # 내보내기
        colx, coly = st.columns(2)
        with colx:
            if st.button("CSV 다운로드"):
                st.download_button("download.csv", sdf.to_csv(index=False).encode("utf-8-sig"),
                                 file_name="velos_export.csv")
        with coly:
            if st.button("Markdown+CSV ZIP"):
                buff = io.BytesIO()
                with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("velos_export.csv", sdf.to_csv(index=False))
                    md = "\n\n".join([f"### {r.time} [{r.role}]  \n{r.content}"
                                     for r in sdf.itertuples()])
                    zf.writestr("velos_export.md", md)
                st.download_button("download.zip", buff.getvalue(), file_name="velos_export.zip")
    else:
        st.warning("데이터를 로드할 수 없습니다. 모듈이 올바르게 설치되었는지 확인하세요.")

with tab2:
    st.subheader("🧵 스레드(대화 단위) 보기")
    session_id = st.text_input("세션ID(빈칸이면 최근 세션)")
    thread = load_conversations(days=days, limit=5000)

    if not thread.empty:
        if session_id:
            thread = thread[thread["session"] == session_id]

        # turn 단위 묶기
        grp = {}
        for r in thread.itertuples():
            key = f"{r.session}:{r.turn or 0}"
            grp.setdefault(key, []).append(r)

        for key, msgs in list(grp.items())[:50]:
            with st.expander(f"{key} · {len(msgs)}메시지"):
                for r in msgs:
                    body = scrub_text(r.content) if pii_mask and PII_AVAILABLE else r.content
                    st.markdown(f"**{r.time} — {r.role}**  \n{body}")
    else:
        st.warning("스레드 데이터를 로드할 수 없습니다.")

with tab3:
    st.subheader("🧠 의미기반 검색(벡터)")
    if not VECTOR_AVAILABLE:
        st.warning("⚠️ 벡터 검색 모듈을 사용할 수 없습니다.")

    query = st.text_input("자연어로 물어보세요", "")
    k = st.slider("Top-K", 3, 50, 10)

    if st.button("의미 검색 실행") and query.strip():
        res = embed_search(query=query, topk=k, days=days)
        st.write(res)

with tab4:
    st.subheader("📈 시스템/리포트")
    m = load_system_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("메모리 사용량", m.get("mem", "-"))
    c2.metric("CPU 사용량", m.get("cpu", "-"))
    c3.metric("활성 세션", m.get("sessions", "-"))
    st.caption("리포트 파일/디스패치 로그는 좌측 경로에서 확인하세요.")

# -------- 푸터 --------
st.markdown("---")
st.caption(f"VELOS ROOT: {ROOT} • 모듈 상태: {'✅' if MODULES_AVAILABLE else '⚠️'} • 마지막 갱신: {time.strftime('%Y-%m-%d %H:%M:%S')}")
