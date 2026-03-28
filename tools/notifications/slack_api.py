#!/usr/bin/env python3
# Minimal Slack sender used by CI. Falls back to no-op if env missing.
import os, json, urllib.request

API_URL = 'https://slack.com/api/chat.postMessage'

def send(text: str) -> bool:
    token = os.environ.get('SLACK_BOT_TOKEN')
    channel = os.environ.get('SLACK_CHANNEL_ID')
    if not token or not channel:
        print('[slack_api] missing env, noop:', text)
        return True  # do not fail CI when env missing
    try:
        data = json.dumps({'channel': channel, 'text': text}).encode('utf-8')
        req = urllib.request.Request(API_URL, data=data, method='POST')
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Authorization', f'Bearer {token}')
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            ok = json.loads(body.decode('utf-8')).get('ok', False)
            print('[slack_api] sent ok=', ok)
            return True  # always return True to avoid CI failure on Slack issues
    except Exception as e:
        print('[slack_api] send failed:', e)
        return True  # never fail CI due to Slack
