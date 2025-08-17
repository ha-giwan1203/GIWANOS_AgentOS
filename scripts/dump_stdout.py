# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

import sys
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

s = sys.stdin.read()
print("REPR:", repr(s))
print("JSON:", json.dumps(s, ensure_ascii=False))
