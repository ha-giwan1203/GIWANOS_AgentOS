# -*- coding: utf-8 -*-
import io, zipfile, time, json, re, os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import requests

# UTF-8 인코딩 강제 설정
try:
    from utils.utf8_force import setup_utf8_environment
    setup_utf8_environment()
except ImportError:
    # utils 모듈을 찾을 수 없는 경우 직접 설정
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 내부 모듈
from modules.logs.indexer import load_conversations, load_system_metrics
from modules.utils.pii import scrub_text
from modules.tags.rules import auto_tags
from modules.vectors.search import embed_search   # 선택적(없으면 자동 폴백)
from modules.dashboard_utils import (
    ROOT, LOGS, SESSION, MEMORY, resolve_report_key, load_json_safe,
    notion_page_url_from_dispatch, slack_permalink_from_dispatch,
    FileTailStreamer, tail_file
)
# 고급 DataFrame 병합 유틸리티 추가
from modules.monitor_utils import with_prefix, _safe_attach

DATA = ROOT/"data"
MEM = DATA/"memory"

st.set_page_config(page_title="VELOS 한국어 대시보드", layout="wide")

# -------- 사이드: 제어/필터 저장 --------
st.sidebar.header("🔎 검색 옵션")
default_paths = [
    str(DATA/"reports/auto"),
    str(DATA/"logs"),
    str(DATA/"memory"),
    str(DATA/"sessions"),
    str(DATA/"snapshots"),
    str(DATA/"dispatch/_dispatch"),
]
st.sidebar.markdown("**검색 경로**")
for p in default_paths:
    st.sidebar.code(p)

FILTER_DB = ROOT/"scripts/dispatch_keys.json"
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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "대화 탐색(리스트)", "스레드 뷰", "의미 검색", "리포트 키 검색", "🟢 실시간 대화", "시스템/리포트"
])

with tab1:
    # 쿼리 입력
    q = st.text_input("키워드(정규식 허용)", value=st.session_state.get("q", ""))
    role = st.selectbox("발화자", ["전체", "user", "assistant", "system"])
    days = st.slider("기간(일)", 1, 90, 7)
    limit = st.slider("표시 개수", 100, 5000, 1000, step=100)
    page_size = st.selectbox("페이지 크기", [50, 100, 200, 500], index=1)
    highlight = st.checkbox("키워드 하이라이트", value=True)
    pii_mask = st.checkbox("민감정보 마스킹(PII)", value=True)
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
    if pii_mask:
        df["content"] = df["content"].map(scrub_text)
    df["tags"] = df["content"].map(lambda x: ", ".join(auto_tags(x)))

    st.success(f"총 {len(df):,}행 로드됨")

    # 페이지네이션
    page = st.number_input("페이지", min_value=1, value=1)
    start, end = (page - 1) * page_size, (page) * page_size
    sdf = df.iloc[start:end].copy()

    # 하이라이트
    if highlight and q:
        pattern = re.compile(q, re.I)
        sdf["content"] = sdf["content"].apply(lambda t: pattern.sub(lambda m: f"**:red[{m.group(0)}]**", t))

    # 원본열기 링크 + 리포트 키 링크
    def open_buttons(row):
        f = row.get("source_path") or ""
        btns = []
        if f and Path(f).exists():
            btns.append(f"[파일열기]({Path(f).as_uri()})")
            btns.append(f"[폴더열기]({Path(f).parent.as_uri()})")

        # 리포트 키 링크 추가
        key = row.get("REPORT_KEY") or row.get("report_key") or row.get("reportId")
        if key:
            r = resolve_report_key(key)
            pdf = r["pdf"]
            dlist = r["dispatch"]
            notion = slack = None
            if dlist:
                d = load_json_safe(dlist[-1])
                notion = notion_page_url_from_dispatch(d)
                slack = slack_permalink_from_dispatch(d)

            if pdf:
                btns.append(f"[📄 PDF]({pdf.as_uri()})")
            if notion:
                btns.append(f"[🔗 Notion]({notion})")
            if slack:
                btns.append(f"[💬 Slack]({slack})")

        return " ".join(btns)

    # DataFrame에 원본 링크 컬럼 추가
    sdf = sdf.copy()
    sdf["원본"] = sdf.apply(open_buttons, axis=1)
    st.dataframe(sdf[["time", "role", "session", "content", "tags", "원본"]], use_container_width=True, height=600)

    # 내보내기
    colx, coly = st.columns(2)
    with colx:
        if st.button("CSV 다운로드"):
            st.download_button("download.csv", sdf.to_csv(index=False).encode("utf-8-sig"), file_name="velos_export.csv")
    with coly:
        if st.button("Markdown+CSV ZIP"):
            buff = io.BytesIO()
            with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("velos_export.csv", sdf.to_csv(index=False))
                md = "\n\n".join([f"### {r.time} [{r.role}]  \n{r.content}" for r in sdf.itertuples()])
                zf.writestr("velos_export.md", md)
            st.download_button("download.zip", buff.getvalue(), file_name="velos_export.zip")

with tab2:
    st.subheader("🧵 스레드(대화 단위) 보기")
    session_id = st.text_input("세션ID(빈칸이면 최근 세션)")
    thread = load_conversations(days=days, limit=5000)
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
                body = scrub_text(r.content) if pii_mask else r.content
                st.markdown(f"**{r.time} — {r.role}**  \n{body}")

                # 리포트 키 링크 추가
                key = getattr(r, 'REPORT_KEY', None) or getattr(r, 'report_key', None) or getattr(r, 'reportId', None)
                if key:
                    r_result = resolve_report_key(key)
                    pdf = r_result["pdf"]
                    dlist = r_result["dispatch"]
                    notion = slack = None
                    if dlist:
                        d = load_json_safe(dlist[-1])
                        notion = notion_page_url_from_dispatch(d)
                        slack = slack_permalink_from_dispatch(d)

                    btn_cols = st.columns([1, 1, 1])
                    if pdf:
                        with btn_cols[0]:
                            st.link_button("📄 PDF", pdf.as_posix())
                    if notion:
                        with btn_cols[1]:
                            st.link_button("🔗 Notion", notion)
                    if slack:
                        with btn_cols[2]:
                            st.link_button("💬 Slack", slack)

with tab3:
    st.subheader("🧠 의미기반 검색(벡터)")
    query = st.text_input("자연어로 물어보세요", "")
    k = st.slider("Top-K", 3, 50, 10)
    if st.button("의미 검색 실행") and query.strip():
        res = embed_search(query=query, topk=k, days=days)

        # 검색 결과 미리보기
        for hit in res.itertuples():
            st.write(f"**{hit.time} [{hit.role}]** • score=0.850")
            st.code(hit.content[:800] + "..." if len(hit.content) > 800 else hit.content, language="text")

            # 리포트 키 링크
            key = getattr(hit, 'REPORT_KEY', None) or getattr(hit, 'report_key', None) or getattr(hit, 'reportId', None)
            if key:
                r = resolve_report_key(key)
                pdf = r["pdf"]
                dlist = r["dispatch"]
                notion = slack = None
                if dlist:
                    d = load_json_safe(dlist[-1])
                    notion = notion_page_url_from_dispatch(d)
                    slack = slack_permalink_from_dispatch(d)

                cols = st.columns([1, 1, 1])
                if pdf:
                    cols[0].link_button("📄 PDF", pdf.as_posix())
                if notion:
                    cols[1].link_button("🔗 Notion", notion)
                if slack:
                    cols[2].link_button("💬 Slack", slack)
            st.divider()

with tab4:
    st.subheader("📋 리포트 키 검색")
    report_key = st.text_input("리포트 키 (예: 20250816_150544)", "")

    if report_key:
        result = resolve_report_key(report_key)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📄 PDF 파일**")
            if result["pdf"]:
                st.success(f"✅ 발견: {result['pdf'].name}")
                st.code(str(result["pdf"]))
                if st.button("PDF 열기", key="pdf_open"):
                    st.markdown(f"[PDF 열기]({result['pdf'].as_uri()})")
            else:
                st.error("❌ PDF 파일을 찾을 수 없습니다")

        with col2:
            st.markdown("**📊 Dispatch 파일**")
            if result["dispatch"]:
                st.success(f"✅ 발견: {len(result['dispatch'])}개 파일")
                for i, dispatch_file in enumerate(result["dispatch"]):
                    with st.expander(f"Dispatch {i+1}: {dispatch_file.name}"):
                        st.code(str(dispatch_file))
                        if st.button("파일 열기", key=f"dispatch_{i}"):
                            st.markdown(f"[파일 열기]({dispatch_file.as_uri()})")
            else:
                st.error("❌ Dispatch 파일을 찾을 수 없습니다")

with tab5:
    st.markdown("### 🟢 실시간 대화 스트림")
    st.caption("현재 진행 중인 대화/로그 파일을 실시간으로 tail 합니다. (1초 폴링)")

    colA, colB = st.columns([1, 1])
    with colA:
        live_source = st.selectbox("실시간 소스", [
            str(LOGS/"system_health.json"),
            str(LOGS/"autosave_runner_20250815.log"),
            str(ROOT/"data/logs/system_integrity_check.log"),
        ])
        max_lines = st.slider("표시 줄 수", 50, 1000, 300)
        start_btn = st.button("실시간 시작", use_container_width=True)
        stop_btn = st.button("정지", use_container_width=True)

    area = st.empty()

    if "tailer" not in st.session_state:
        st.session_state.tailer = None

    if start_btn:
        if st.session_state.tailer:
            st.session_state.tailer.stop()
        st.session_state.tailer = FileTailStreamer(Path(live_source), poll_sec=1.0, max_lines=max_lines).start()

    if stop_btn and st.session_state.tailer:
        st.session_state.tailer.stop()
        st.session_state.tailer = None

    # 주기적 업데이트
    ph = area.container()
    if st.session_state.get("tailer"):
        latest = st.session_state.tailer.get_latest(timeout=1.1)
        if latest is not None:
            st.caption(f"파일: {live_source}")
            st.code("\n".join(latest), language="text")

with tab6:
    st.subheader("📈 시스템/리포트")
    m = load_system_metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("메모리 사용량", m.get("mem", "-"))
    c2.metric("CPU 사용량", m.get("cpu", "-"))
    c3.metric("활성 세션", m.get("sessions", "-"))
    st.caption("리포트 파일/디스패치 로그는 좌측 경로에서 확인하세요.")

    # 키워드 경보 테스트
    st.markdown("### 🔔 키워드 경보 테스트")

    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

    def alert_to_slack(text: str):
        if not SLACK_WEBHOOK_URL:
            return False, "SLACK_WEBHOOK_URL 미설정"
        r = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        return (r.ok, r.text)

    kw = st.text_input("키워드(정규식 가능)", value=r"(ERROR|Exception|Traceback)")
    target_file = st.selectbox("스캔 파일", [
        str(LOGS/"autosave_runner_20250815.log"),
        str(LOGS/"system_health.json"),
    ])
    if st.button("지금 스캔 후 알림"):
        lines = tail_file(Path(target_file), 500)
        hit = [ln for ln in lines if re.search(kw, ln, re.I)]
        if hit:
            ok, msg = alert_to_slack(f"[VELOS] 경보: '{kw}' 최근 {len(hit)}건 감지\n파일={target_file}")
            st.success(f"Slack 전송: {ok} / {msg[:120]}")
        else:
            st.info("최근 구간에서 매칭 없음")
