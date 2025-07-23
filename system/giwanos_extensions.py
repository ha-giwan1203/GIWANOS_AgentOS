#!/usr/bin/env python
"""
GIWANOS Extensions Bundle
 - UI/대시보드 확장 (Streamlit 기반)
 - Notion ↔ GitHub 동기화 워크플로우 구현 (issues → Notion DB)
 - 릴리스 자동화 강화 (Git 태그, ZIP 패키징, GitHub 릴리즈)
파일명을 변경하지 않고 기존 프로젝트 구조에 덮어쓰실 수 있습니다.
"""
import os
import io
import sys
from datetime import datetime

# ─── .env 파일 로드 ──────────────────────────────────────
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r', encoding='utf-8') as envf:
        for line in envf:
            if not line.strip() or line.strip().startswith('#'):
                continue
            if '=' in line:
                k, v = line.strip().split('=', 1)
                os.environ.setdefault(k, v)
# ────────────────────────────────────────────────────────

# ──────────────── 1. Streamlit Dashboard 확장 ────────────────
import streamlit as st

def render_dashboard():
    st.title("GIWANOS 운영체계 대시보드")

    # 메모리 로그 목록
    logs = sorted([f for f in os.listdir('logs') if f.startswith('memory')], reverse=True)
    st.sidebar.header("메모리 로그")
    st.sidebar.write(logs[:5] or "없음")

    # 최근 백업 파일
    backups = sorted(os.listdir('loop_backups'), reverse=True)
    st.subheader("최근 백업 파일")
    st.write(backups[:5] or "없음")

    # 동기화 상태 (예시)
    st.subheader("동기화 상태")
    st.markdown("- Notion: ✅ 최신 항목 동기화됨")
    st.markdown("- GitHub: ✅ 최근 커밋 반영됨")

    # 릴리스 아티팩트
    releases = sorted([f for f in os.listdir('github_release_bundle') if f.endswith('.zip')], reverse=True)
    st.subheader("릴리스 아티팩트")
    st.write(releases[:3] or "없음")

if __name__ == '__main__':
    render_dashboard()

# ────────────── 2. Notion ↔ GitHub 동기화 스크립트 ─────────────
import requests

def sync_github_to_notion(owner, repo, notion_db_id):
    """
    GitHub 리포지토리의 이슈를 Notion 데이터베이스에 동기화합니다.
    owner: GitHub 사용자/조직
    repo: 리포지토리 이름
    notion_db_id: Notion 데이터베이스 ID
    """
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Error: GITHUB_TOKEN 환경변수가 설정되지 않았습니다.")
        return
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {'Authorization': f"token {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"GitHub API error: {resp.status_code} - {resp.text}")
        return
    issues = resp.json()
    if not isinstance(issues, list):
        print(f"Unexpected API response: {issues}")
        return

    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print("Error: NOTION_TOKEN 환경변수가 설정되지 않았습니다.")
        return
    notion_endpoint = 'https://api.notion.com/v1/pages'
    for issue in issues:
        title = issue.get('title')
        html_url = issue.get('html_url')
        if not title or not html_url:
            continue
        data = {
            "parent": {"database_id": notion_db_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "URL": {"url": html_url}
            }
        }
        r = requests.post(notion_endpoint,
                          headers={
                              'Authorization': f"Bearer {notion_token}",
                              'Notion-Version': '2022-06-28',
                              'Content-Type': 'application/json'
                          },
                          json=data)
        print(f"Notion sync status for '{title}': {r.status_code}")

# ───────────── 3. 릴리스 자동화 스크립트 ─────────────
import shutil

def automate_release(version_tag):
    """
    Git 태그 생성, ZIP 패키징, GitHub 릴리즈를 자동화합니다.
    version_tag: 릴리스 태그 이름 (예: 'v1.2.3')
    """
    # 1) Git 태그 생성 및 푸시
    os.system(f"git tag {version_tag}")
    os.system(f"git push origin {version_tag}")

    # 2) ZIP 패키지 생성
    zip_name = f"giwanos_release_{version_tag}.zip"
    shutil.make_archive(f"giwanos_release_{version_tag}", 'zip', root_dir='.', base_dir='.')
    print(f"Package created: {zip_name}")

    # 3) GitHub 릴리즈 생성 (gh CLI 필요)
    os.system(
        f"gh release create {version_tag} {zip_name} --title \"GIWANOS {version_tag}\" --notes \"Release {version_tag} on {datetime.now():%Y-%m-%d}\""
    )
    print(f"Release {version_tag} completed.")