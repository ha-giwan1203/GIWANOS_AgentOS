#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 7 — Slack 보고 이미지 발송
v1: 월간 조립비 대시보드 PNG + 인사이트 3줄 Slack 업로드

입력:  _cache/월간_조립비_대시보드.png
       _cache/step7_visualization_input.json
출력:  Slack 채널에 PNG + initial_comment 발송

API 흐름 (Slack files v2):
  1. files.getUploadURLExternal  → upload_url, file_id
  2. upload_url 에 PNG raw bytes POST
  3. files.completeUploadExternal → 채널 공유 완료

실행:
    python step7_slack_보고.py
    python step7_slack_보고.py --dry-run
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from _pipeline_config import CACHE_DIR

PNG_FILE  = os.path.join(CACHE_DIR, '월간_조립비_대시보드.png')
VIS_INPUT = os.path.join(CACHE_DIR, 'step7_visualization_input.json')

SLACK_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / '90_공통기준/업무관리/slack_config.yaml'

print("=" * 60)
print("Step 7: Slack 보고 이미지 발송")
print("=" * 60)


# ── 설정 / 토큰 로드 ──────────────────────────────────────────
def _load_config():
    import yaml
    with open(SLACK_CONFIG_PATH, encoding='utf-8') as f:
        return yaml.safe_load(f)

def _load_token(cfg: dict) -> str:
    env_key = cfg['slack'].get('token_env', 'SLACK_BOT_TOKEN')
    token = os.environ.get(env_key, '')
    if token.startswith('xoxb-') or token.startswith('xoxp-'):
        return token
    fallback = cfg['slack'].get('token_env_fallback_path', '')
    if fallback and Path(fallback).exists():
        for line in Path(fallback).read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if line.startswith(env_key + '='):
                val = line.split('=', 1)[1].strip().strip('"').strip("'")
                if val.startswith('xoxb-') or val.startswith('xoxp-'):
                    return val
    return ''


# ── Slack API 3단계 ───────────────────────────────────────────

def _get_upload_url(token: str, filename: str, length: int) -> tuple:
    """1단계: upload URL + file_id 획득."""
    url = 'https://slack.com/api/files.getUploadURLExternal'
    params = urllib.parse.urlencode({'filename': filename, 'length': length})
    req = urllib.request.Request(f"{url}?{params}", method='GET',
                                  headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode('utf-8'))
    if not body.get('ok'):
        raise RuntimeError(f"getUploadURLExternal 실패: {body.get('error')}")
    return body['upload_url'], body['file_id']


def _upload_bytes(upload_url: str, png_path: str) -> bool:
    """2단계: upload_url에 PNG raw bytes POST."""
    data = Path(png_path).read_bytes()
    req = urllib.request.Request(upload_url, data=data, method='POST',
                                  headers={'Content-Type': 'application/octet-stream'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = resp.status
    return status == 200


def _complete_upload(token: str, file_id: str, channel_id: str,
                     title: str, initial_comment: str) -> bool:
    """3단계: 채널 공유 완료."""
    url = 'https://slack.com/api/files.completeUploadExternal'
    payload = json.dumps({
        'files': [{'id': file_id, 'title': title}],
        'channel_id': channel_id,
        'initial_comment': initial_comment,
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method='POST', headers={
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {token}',
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode('utf-8'))
    if not body.get('ok'):
        raise RuntimeError(f"completeUploadExternal 실패: {body.get('error')}")
    return True


def _fallback_text(token: str, channel_id: str, text: str, mention: str) -> bool:
    """PNG 업로드 실패 시 텍스트-only fallback."""
    url = 'https://slack.com/api/chat.postMessage'
    payload = json.dumps({
        'channel': channel_id,
        'text': f"<@{mention}> {text}" if mention else text,
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method='POST', headers={
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {token}',
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode('utf-8'))
    return body.get('ok', False)


# ── 메인 ──────────────────────────────────────────────────────
def main(dry_run: bool = False):
    # 입력 파일 확인
    if not Path(PNG_FILE).exists():
        print(f"[ERROR] PNG 없음: {PNG_FILE}")
        print("  먼저 step7_대시보드.py 를 실행하세요.")
        sys.exit(1)
    if not Path(VIS_INPUT).exists():
        print(f"[ERROR] visualization_input 없음: {VIS_INPUT}")
        sys.exit(1)

    # visualization_input에서 인사이트 로드
    with open(VIS_INPUT, encoding='utf-8') as f:
        vis = json.load(f)
    insights = vis.get('insights', [])
    meta = vis.get('report_meta', {})
    summary = vis.get('summary', {})

    base_month = meta.get('base_month', '')
    total_cost = summary.get('total_cost', 0)
    validation = summary.get('validation_result', 'N/A')
    anomaly_cnt = summary.get('anomaly_count', 0)

    # initial_comment 구성
    insight_text = '\n'.join(f"  {i+1}. {ins}" for i, ins in enumerate(insights))
    initial_comment = (
        f"[{base_month}] 월간 조립비 정산 대시보드\n"
        f"총 조립비: {total_cost:,}원  |  검증: {validation}  |  이상치: {anomaly_cnt}건\n\n"
        f"{insight_text}"
    )

    png_size = Path(PNG_FILE).stat().st_size
    filename  = f"{base_month}_조립비_대시보드.png"
    title     = f"{base_month} 월간 조립비 정산 대시보드"

    print(f"[INFO] PNG: {png_size:,} bytes")
    print(f"[INFO] 채널 메시지 미리보기:")
    print(f"  {initial_comment}")

    if dry_run:
        print("\n[DRY-RUN] 발송 건너뜀.")
        return

    # 설정 / 토큰 로드
    cfg = _load_config()
    token = _load_token(cfg)
    if not token:
        print("[ERROR] Slack Bot Token 없음. 환경변수 SLACK_BOT_TOKEN 또는 .env 확인.")
        sys.exit(1)

    channel_id = cfg['slack']['channel_id']
    mention    = cfg['slack'].get('mention_user_id', '')

    try:
        print("[1/3] upload URL 요청 중...")
        upload_url, file_id = _get_upload_url(token, filename, png_size)
        print(f"      file_id: {file_id}")

        print("[2/3] PNG 업로드 중...")
        ok = _upload_bytes(upload_url, PNG_FILE)
        if not ok:
            raise RuntimeError("upload HTTP 응답 비정상")

        print("[3/3] 채널 공유 완료 요청 중...")
        _complete_upload(token, file_id, channel_id, title, initial_comment)

        print(f"\n[완료] Slack 채널({channel_id}) 발송 성공")

    except Exception as e:
        print(f"[ERROR] PNG 업로드 실패: {e}")
        print("[FALLBACK] 텍스트-only 발송 시도...")
        fallback_msg = f"[{base_month}] 월간 조립비 정산 대시보드 (PNG 첨부 실패)\n{initial_comment}"
        ok = _fallback_text(token, channel_id, fallback_msg, mention)
        if ok:
            print("[FALLBACK] 텍스트 발송 성공")
        else:
            print("[FALLBACK] 텍스트 발송도 실패")
            sys.exit(1)

    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='발송 없이 미리보기만')
    args = parser.parse_args()
    main(dry_run=args.dry_run)
