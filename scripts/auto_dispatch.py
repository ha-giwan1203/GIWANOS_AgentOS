# scripts/auto_dispatch.py
from __future__ import annotations
import os, sys, time
from pathlib import Path

# --- 환경변수 로딩 ---
from env_loader import load_env
load_env()

def auto_dispatch():
    """자동 디스패치 실행"""
    print("🚀 VELOS 자동 디스패치 시작")
    print("=" * 40)

    # 경로 설정
    auto_dir = Path(r"C:\giwanos\data\reports\auto")

    # 최신 파일 찾기
    try:
        latest_pdf = max(auto_dir.glob("velos_auto_report_*_ko.pdf"))
        latest_md = max(auto_dir.glob("velos_auto_report_*.md"), default=None)

        print("📄 최신 파일:")
        print(f"   PDF: {latest_pdf.name}")
        if latest_md:
            print(f"   MD:  {latest_md.name}")
        else:
            print("   MD:  없음")

    except ValueError:
        print("❌ PDF 파일을 찾을 수 없습니다")
        return False

    # 디스패치 실행
    print("\n📤 자동 디스패치 실행 중...")
    try:
        from dispatch_report import dispatch_report

        results = dispatch_report(latest_pdf, latest_md, title="VELOS 한국어 종합 보고서")

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

def main():
    """메인 실행 함수"""
    success = auto_dispatch()

    if success:
        print("\n🎉 자동 디스패치 성공!")
        return 0
    else:
        print("\n❌ 자동 디스패치 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())
