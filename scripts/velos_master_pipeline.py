# -*- coding: utf-8 -*-
"""
VELOS 마스터 파이프라인
- 한국어 PDF 보고서 생성
- 멀티 채널 디스패치
- 결과 요약 및 로깅
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 환경변수 로딩
def load_env():
    """환경변수 로딩 및 검증."""
    env_vars = [
        "VELOS_ROOT", "SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID",
        "NOTION_TOKEN", "NOTION_DATABASE_ID"
    ]

    missing = []
    for var in env_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"⚠️  경고: 다음 환경변수가 없습니다: {', '.join(missing)}")

    return len(missing) == 0

def run_pdf_generation():
    """PDF 보고서 생성."""
    print("📊 PDF 보고서 생성 중...")
    try:
        from generate_velos_report_ko import main as generate_pdf
        generate_pdf()
        print("✅ PDF 보고서 생성 완료")
        return True
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        return False

def run_dispatch():
    """멀티 채널 디스패치 실행."""
    print("📤 멀티 채널 디스패치 실행 중...")
    try:
        from dispatch_report import dispatch_report

        # 최신 파일 찾기
        auto_dir = Path("C:/giwanos/data/reports/auto")
        latest_pdf = max(auto_dir.glob("velos_auto_report_*_ko.pdf"), default=None)
        latest_md = max(auto_dir.glob("velos_auto_report_*.md"), default=None)

        if not latest_pdf:
            print("❌ PDF 파일을 찾을 수 없습니다")
            return False

        results = dispatch_report(latest_pdf, latest_md)

        # 결과 분석
        success_count = sum(1 for v in results.values() if isinstance(v, dict) and v.get("ok"))
        total_count = len([k for k in results.keys() if k in ["slack", "notion", "email", "push"]])

        print(f"✅ 디스패치 완료: {success_count}/{total_count} 채널 성공")

        # 실패한 채널 출력
        for channel, result in results.items():
            if isinstance(result, dict) and not result.get("ok"):
                print(f"   ⚠️  {channel}: {result.get('detail', 'unknown error')}")

        return success_count > 0
    except Exception as e:
        print(f"❌ 디스패치 실패: {e}")
        return False

def create_summary():
    """실행 요약 생성."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "steps": {
            "env_check": load_env(),
            "pdf_generation": run_pdf_generation(),
            "dispatch": run_dispatch()
        }
    }

    # 요약 저장
    summary_file = Path("C:/giwanos/data/reports/auto/pipeline_summary.json")
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return summary

def main():
    """메인 파이프라인 실행."""
    print("🚀 VELOS 마스터 파이프라인 시작")
    print("=" * 50)

    start_time = time.time()

    # 1. 환경변수 검증
    print("🔧 환경변수 검증...")
    env_ok = load_env()

    # 2. PDF 생성
    pdf_ok = run_pdf_generation()

    # 3. 디스패치
    dispatch_ok = run_dispatch()

    # 4. 요약 생성
    summary = create_summary()

    # 5. 결과 출력
    elapsed = time.time() - start_time
    print("=" * 50)
    print("📋 실행 요약:")
    print(f"   환경변수: {'✅' if env_ok else '❌'}")
    print(f"   PDF 생성: {'✅' if pdf_ok else '❌'}")
    print(f"   디스패치: {'✅' if dispatch_ok else '❌'}")
    print(f"   소요시간: {elapsed:.1f}초")

    if pdf_ok and dispatch_ok:
        print("🎉 VELOS 파이프라인 성공 완료!")
        return 0
    else:
        print("⚠️  일부 단계에서 문제가 발생했습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
