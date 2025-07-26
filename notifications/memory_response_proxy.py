import sys
import io

# 윈도우 콘솔을 UTF-8로 재설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json

def is_allowed_request(request_text):
    banned_keywords = ["v13", "진화", "확장", "버전", "다음 단계"]
    for word in banned_keywords:
        if word in request_text:
            return False
    return True

if __name__ == "__main__":
    test = "v13 확장 계획이 어떻게 되죠?"
    if not is_allowed_request(test):
        print("🚫 요청 차단됨: 시스템은 고정 상태입니다.")
    else:
        print("✅ 요청 허용됨")