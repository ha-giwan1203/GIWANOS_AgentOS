# [ACTIVE] VELOS 대시보드: REPORT_KEY로 관련 리포트/로그/메모리/노션/슬랙을 한 번에 검색
# -*- coding: utf-8 -*-
# 실행: streamlit run velos_dashboard.py
# 필요(선택): NOTION_TOKEN, NOTION_DATABASE_ID, SLACK_BOT_TOKEN
import os
import re
import json
import glob
import sys
import datetime as dt
from pathlib import Path
from typing import Dict, List, Any

import streamlit as st

# UTF-8 인코딩 강제 설정
try:
    from modules.utils.utf8_force import setup_utf8_environment
    setup_utf8_environment()
except ImportError:
    # utils 모듈을 찾을 수 없는 경우 직접 설정
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────────────
# 경로 설정
ROOT = Path(r"C:\giwanos")
LOGS = ROOT / "data" / "logs"
REPORT = ROOT / "data" / "reports"
AUTO = REPORT / "auto"
REFL = ROOT / "data" / "reflections"
DISP = REPORT / "_dispatch"
MEMORY = ROOT / "data" / "memory"
SESSIONS = ROOT / "data" / "sessions"
SNAPSHOTS = ROOT / "data" / "snapshots"

# ──────────────────────────────────────────────────────────────────────────────
# 유틸
def safe_json_load(path: Path) -> Any:
    """안전한 JSON 로드"""
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def read_text(path: Path, tail: int = None) -> str:
    """파일 내용 읽기 (tail 옵션 지원)"""
    if not path.exists():
        return ""
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if tail and tail > 0:
        lines = txt.splitlines()
        return "\n".join(lines[-tail:])
    return txt


def find_files_containing(report_key: str, patterns: List[str], dirs: List[Path]) -> List[Path]:
    """REPORT_KEY가 포함된 파일들 찾기"""
    hits = []
    for d in dirs:
        if not d.exists():
            continue
        for pat in patterns:
            for p in d.glob(pat):
                try:
                    # 파일명에 포함되면 바로 채택
                    if report_key in p.name:
                        hits.append(p)
                        continue
                    # 텍스트 파일만 내용 스캔
                    if p.suffix.lower() in {".txt", ".json", ".md", ".log", ".yaml", ".yml"}:
                        if report_key in read_text(p):
                            hits.append(p)
                except Exception:
                    pass
    # 중복 제거 + 최신순
    uniq = {str(p): p for p in hits}.values()
    return sorted(uniq, key=lambda x: x.stat().st_mtime, reverse=True)


def to_notion_url(page_id: str) -> str:
    """Notion 페이지 URL 생성"""
    return f"https://www.notion.so/{page_id.replace('-', '')}"


def format_file_size(size_bytes: int) -> str:
    """파일 크기 포맷팅"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


# ──────────────────────────────────────────────────────────────────────────────
# Notion 검색(옵션)
def notion_search_by_report_key(report_key: str) -> Dict[str, Any]:
    """Notion DB에서 REPORT_KEY로 검색"""
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DATABASE_ID")
    result_prop = os.getenv("NOTION_RESULTID_PROP", "결과 ID")

    if not token or not db_id:
        return {"enabled": False, "reason": "NOTION_TOKEN/NOTION_DATABASE_ID 없음"}

    try:
        import requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        # 데이터베이스 쿼리(간단 필터)
        payload = {
            "filter": {
                "property": result_prop,
                "rich_text": {"contains": report_key}
            },
            "page_size": 10
        }
        r = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=headers, json=payload, timeout=15
        )
        if r.status_code not in (200, 201):
            return {
                "enabled": True,
                "ok": False,
                "status": r.status_code,
                "body": r.text[:400]
            }

        data = r.json()
        rows = []
        for it in data.get("results", []):
            page_id = it.get("id")
            props = it.get("properties", {})
            # 제목 추출(스키마마다 다르니 최대공약수로 처리)
            title_txt = ""
            for v in props.values():
                if isinstance(v, dict) and "title" in v:
                    if v["title"]:
                        title_txt = (
                            v["title"][0].get("plain_text", "") or
                            v["title"][0].get("text", {}).get("content", "")
                        )
                        break
            rows.append({
                "page_id": page_id,
                "url": to_notion_url(page_id) if page_id else "",
                "title": title_txt,
                "created_time": it.get("created_time", ""),
            })
        return {"enabled": True, "ok": True, "rows": rows}

    except Exception as e:
        return {"enabled": True, "ok": False, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Slack 검색(옵션): 봇 토큰으로 간단 검색
def slack_search_by_report_key(report_key: str) -> Dict[str, Any]:
    """Slack에서 REPORT_KEY로 메시지 검색"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        return {"enabled": False, "reason": "SLACK_BOT_TOKEN 없음"}

    try:
        import requests
        # search.messages 는 엔터프라이즈/권한에 따라 제한이 있을 수 있음.
        # 실패해도 대시보드 전체엔 영향 주지 않음.
        r = requests.get(
            "https://slack.com/api/search.messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"query": report_key, "count": 10},
            timeout=15
        )
        data = r.json()
        if not data.get("ok"):
            return {"enabled": True, "ok": False, "body": data}

        rows = []
        for m in data.get("messages", {}).get("matches", []):
            rows.append({
                "permalink": m.get("permalink", ""),
                "channel": m.get("channel", {}).get("name", ""),
                "username": m.get("username", ""),
                "text": m.get("text", ""),
                "ts": m.get("ts", ""),
            })
        return {"enabled": True, "ok": True, "rows": rows}

    except Exception as e:
        return {"enabled": True, "ok": False, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Streamlit UI
st.set_page_config(
    page_title="VELOS REPORT_KEY 대시보드",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 VELOS REPORT_KEY 대시보드")
st.markdown("REPORT_KEY로 모든 관련 정보를 한 번에 검색하고 표시합니다.")

# 상단 입력
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    report_key = st.text_input(
        "REPORT_KEY 입력",
        placeholder="예: 20250816_170736_a45102c4",
        help="검색할 REPORT_KEY를 입력하세요"
    )
with c2:
    tail_lines = st.number_input(
        "로그 Tail 라인수",
        min_value=20,
        max_value=500,
        value=120,
        step=10
    )
with c3:
    run_btn = st.button("🔍 검색 실행", type="primary")

st.caption("💡 토큰/키가 없으면 해당 섹션은 자동 비활성화됩니다.")

if run_btn and report_key:
    if len(report_key) < 10:
        st.error("❌ REPORT_KEY가 너무 짧습니다. 올바른 형식을 확인해주세요.")
        st.info("올바른 형식: YYYYMMDD_HHMMSS_xxxxxxxx")
    else:
        with st.spinner("🔍 검색 중..."):
            # 파일/로그 탐색
            st.subheader("📄 로컬 파일 히트")
            patterns = ["*.json", "*.log", "*.md", "*.txt", "*.pdf", "*.html", "*.yaml", "*.yml"]
            dirs = [LOGS, REPORT, AUTO, REFL, DISP, MEMORY, SESSIONS, SNAPSHOTS]
            hits = find_files_containing(report_key, patterns, dirs)

            if not hits:
                st.info("로컬에서 해당 REPORT_KEY가 포함된 항목을 찾지 못했습니다.")
            else:
                st.success(f"총 {len(hits)}개의 관련 파일을 찾았습니다.")

                # 파일 목록을 카테고리별로 분류
                categories = {
                    "로그": [],
                    "보고서": [],
                    "회고": [],
                    "메모리": [],
                    "세션": [],
                    "스냅샷": [],
                    "기타": []
                }

                for p in hits[:100]:
                    if "logs" in str(p):
                        categories["로그"].append(p)
                    elif "reports" in str(p):
                        categories["보고서"].append(p)
                    elif "reflections" in str(p):
                        categories["회고"].append(p)
                    elif "memory" in str(p):
                        categories["메모리"].append(p)
                    elif "sessions" in str(p):
                        categories["세션"].append(p)
                    elif "snapshots" in str(p):
                        categories["스냅샷"].append(p)
                    else:
                        categories["기타"].append(p)

                # 카테고리별로 표시
                for category, files in categories.items():
                    if files:
                        with st.expander(f"📂 {category} ({len(files)}개)"):
                            for p in files:
                                try:
                                    size = format_file_size(p.stat().st_size)
                                    modified = dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                                    st.write(f"📄 **{p.name}**")
                                    st.write(f"   📏 크기: {size} | 🕒 수정: {modified}")
                                    st.code(str(p))
                                except:
                                    st.write(f"📄 {p}")

            # 대표 로그 미리보기
            st.subheader("🧾 로그 미리보기")
            sample_logs = [
                LOGS / "autosave_runner.log",
                LOGS / "autosave_runner_20250815.log",
                LOGS / "system_health.json",
                LOGS / "loop_state_tracker.json"
            ]

            for lp in sample_logs:
                if lp.exists():
                    with st.expander(f"📋 {lp.name}"):
                        content = read_text(lp, tail=tail_lines)
                        if content:
                            st.code(content)
                        else:
                            st.info("파일이 비어있거나 읽을 수 없습니다.")

            # Notion 검색
            st.subheader("🗃️ Notion DB 검색")
            nres = notion_search_by_report_key(report_key)
            if not nres.get("enabled"):
                st.warning(f"⚠️ {nres.get('reason', 'Notion 비활성')}")
            elif not nres.get("ok"):
                st.error(f"❌ Notion 검색 실패: {nres.get('status', '')} {nres.get('body', nres.get('error', ''))}")
            else:
                rows = nres.get("rows", [])
                if not rows:
                    st.info("Notion DB에서 해당 REPORT_KEY를 찾지 못했습니다.")
                else:
                    st.success(f"Notion DB에서 {len(rows)}개의 항목을 찾았습니다.")
                    for r in rows:
                        title = r.get('title') or r.get('page_id', '제목 없음')
                        url = r.get('url', '')
                        created = r.get('created_time', '')

                        if url:
                            st.write(f"- [{title}]({url})")
                        else:
                            st.write(f"- {title}")

                        if created:
                            st.caption(f"  생성: {created[:19]}")

            # Slack 검색
            st.subheader("💬 Slack 메시지 검색")
            sres = slack_search_by_report_key(report_key)
            if not sres.get("enabled"):
                st.warning(f"⚠️ {sres.get('reason', 'Slack 비활성')}")
            elif not sres.get("ok"):
                st.error(f"❌ Slack 검색 실패: {sres.get('body', sres.get('error', ''))}")
            else:
                rows = sres.get("rows", [])
                if not rows:
                    st.info("Slack에서 해당 REPORT_KEY를 찾지 못했습니다.")
                else:
                    st.success(f"Slack에서 {len(rows)}개의 메시지를 찾았습니다.")
                    for r in rows:
                        channel = r.get("channel", "알 수 없음")
                        username = r.get("username", "알 수 없음")
                        permalink = r.get("permalink", "")
                        text = r.get("text", "").replace("\n", " ")
                        ts = r.get("ts", "")

                        if permalink:
                            st.write(f"- **[{channel}]** {username} | [메시지 보기]({permalink})")
                        else:
                            st.write(f"- **[{channel}]** {username}")

                        if text:
                            st.code(text[:500] + ("..." if len(text) > 500 else ""))

                        if ts:
                            try:
                                timestamp = dt.datetime.fromtimestamp(float(ts))
                                st.caption(f"  전송: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                            except:
                                pass

            # 요약 박스
            st.subheader("📊 검색 결과 요약")
            summary = {
                "report_key": report_key,
                "local_files": {
                    "total": len(hits),
                    "categories": {k: len(v) for k, v in categories.items() if v}
                },
                "notion_count": len(nres.get("rows", [])) if nres.get("ok") else 0,
                "slack_count": len(sres.get("rows", [])) if sres.get("ok") else 0,
                "search_time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 요약을 컬럼으로 표시
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📄 로컬 파일", summary["local_files"]["total"])
            with col2:
                st.metric("🗃️ Notion 항목", summary["notion_count"])
            with col3:
                st.metric("💬 Slack 메시지", summary["slack_count"])
            with col4:
                st.metric("🔍 검색 시간", summary["search_time"][11:])

            # 상세 요약 JSON
            with st.expander("📋 상세 요약 JSON"):
                st.json(summary)

elif run_btn and not report_key:
    st.warning("⚠️ REPORT_KEY를 입력해주세요.")

else:
    # 사용법 안내
    st.markdown("""
    ### 🚀 사용법

    1. **REPORT_KEY 입력**: 검색할 REPORT_KEY를 입력하세요
    2. **로그 라인수 설정**: 표시할 로그 라인 수를 설정하세요 (기본: 120줄)
    3. **검색 실행**: 🔍 검색 실행 버튼을 클릭하세요

    ### 📋 REPORT_KEY 형식

    REPORT_KEY는 다음과 같은 형식입니다:
    ```
    YYYYMMDD_HHMMSS_xxxxxxxx
    ```

    - **YYYYMMDD**: 날짜 (예: 20250816)
    - **HHMMSS**: 시간 (예: 170736)
    - **xxxxxxxx**: 고유 ID (8자리)

    ### 🔍 검색 예시

    - `20250816_170736_a45102c4`
    - `20250816_144400_abcd1234`
    - `20250815_090000_12345678`

    ### 📂 검색되는 항목들

    - **📄 로컬 파일**: 로그, 보고서, 회고, 메모리, 세션, 스냅샷
    - **🗃️ Notion DB**: 데이터베이스에서 REPORT_KEY 검색
    - **💬 Slack**: 채널 메시지에서 REPORT_KEY 검색
    - **🧾 로그 미리보기**: 주요 로그 파일의 최근 내용

    ### ⚙️ 환경변수 설정 (선택사항)

    - **NOTION_TOKEN**: Notion API 토큰
    - **NOTION_DATABASE_ID**: Notion 데이터베이스 ID
    - **SLACK_BOT_TOKEN**: Slack 봇 토큰

    환경변수가 없어도 로컬 파일 검색은 정상 작동합니다.
    """)

# 푸터
st.markdown("---")
st.markdown("*VELOS REPORT_KEY 대시보드 - 모든 관련 정보를 한 번에 검색하세요*")

