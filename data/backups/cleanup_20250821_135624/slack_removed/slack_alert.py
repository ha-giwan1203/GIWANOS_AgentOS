# [EXPERIMENT] VELOS Slack 알림 - 외부 통합 모듈
# -*- coding: utf-8 -*-
import os
import re
import time
from pathlib import Path

import requests

WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
LOG = Path(r"C:\giwanos\data\logs\autosave_runner.log")


def error_burst_alert(threshold=50, window_secs=3600):
    if not WEBHOOK or not LOG.exists():
        return
    cutoff = time.time() - window_secs
    count = 0
    for line in LOG.read_text("utf-8", errors="ignore").splitlines():
        if "ERROR" in line or "Exception" in line:
            count += 1
    if count >= threshold:
        requests.post(WEBHOOK, json={"text": f"⚠️ VELOS 오류 급증 감지: {count}건/최근1h"})
