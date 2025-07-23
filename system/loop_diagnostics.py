#!/usr/bin/env python
import sys
# 콘솔 출력을 UTF-8로 설정
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import os
import json

def check_env(keys=["NOTION_TOKEN", "GITHUB_TOKEN"]):
    """
    .env 파일을 읽어 Notion 및 GitHub 토큰 설정 여부를 확인합니다.
    """
    results = {}
    if not os.path.exists(".env"):
        results[".env"] = "❌ 없음"
        return results
    with open(".env", "r", encoding="utf-8") as f:
        lines = f.readlines()
    env_dict = dict(line.strip().split("=", 1) for line in lines if "=" in line)
    for k in keys:
        results[k] = "✅ 설정됨" if env_dict.get(k) else "⚠️ 비어 있음"
    return results

def check_file_exists(files=["loop_memory_state.json", "loop_reflection_log.pdf"]):
    """
    주요 결과 파일 존재 여부를 확인합니다.
    """
    return {f: "✅ 있음" if os.path.exists(f) else "❌ 없음" for f in files}

def diagnose():
    print("🧠 GIWANOS 시스템 상태 진단")
    print("\n📂 파일 상태:")
    for k, v in check_file_exists().items():
        print(f" • {k}: {v}")

    print("\n🔑 환경 변수 상태:")
    for k, v in check_env().items():
        print(f" • {k}: {v}")

if __name__ == "__main__":
    diagnose()
