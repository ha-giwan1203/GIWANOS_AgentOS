#!/usr/bin/env python
import os
import sys
import traceback
import datetime

def get_current_week_summary_path():
    today = datetime.date.today()
    year, week, _ = today.isocalendar()
    return f"summaries/weekly_summary_{year}W{week:02}.md"

def main():
    print("🚀 GIWANOS 마스터 런처 실행 시작")

    module_to_run = "all"
    if len(sys.argv) >= 3 and sys.argv[1] == "--module":
        module_to_run = sys.argv[2]

    try:
        from giwanos.reflection.generate_reflection import run as run_reflect
        from giwanos.reporting.send_reflection_md import run as run_report
        from giwanos.selfcheck_agent import run as run_selfcheck
        from giwanos.reflection.judge_agent import run as run_judge
        from giwanos.reporting.agent_logger import save_agent_status
        from giwanos.reporting.notion_upload_summary import upload_weekly_summary
        from giwanos.reflection.weekly_summary_generator import run as run_weekly_summary
        from write_giwanos_status import write_summary

        if module_to_run in ["all", "reflect"]:
            print("\n📄 회고 생성")
            run_reflect()
            save_agent_status("reflect", "success")

        if module_to_run in ["all", "report"]:
            print("\n📤 보고서 전송")
            run_report()
            save_agent_status("report", "success")

        if module_to_run in ["all", "judge"]:
            print("\n🧠 판단 분석")
            run_judge()
            save_agent_status("judge", "success")

        if module_to_run in ["all", "selfcheck"]:
            print("\n🩺 시스템 점검")
            run_selfcheck()
            save_agent_status("selfcheck", "success")

        if module_to_run in ["all", "summary"]:
            print("\n📝 시스템 상태 요약")
            write_summary()
            save_agent_status("status_summary", "success")

        if module_to_run in ["all", "weekly"]:
            print("\n🧾 주간 회고 요약 생성")
            run_weekly_summary()
            save_agent_status("weekly_summary", "success")

        if module_to_run in ["all", "notion"]:
            print("\n📤 요약 Notion 전송")
            summary_path = get_current_week_summary_path()
            if os.path.exists(summary_path):
                upload_weekly_summary(summary_path)
                save_agent_status("notion_summary_upload", "success")
            else:
                print("⚠️ 요약 파일이 없어 Notion 전송 생략됨")

    except Exception as e:
        print("❌ 런처 실행 중 오류 발생:")
        traceback.print_exc()
        try:
            from giwanos.reporting.agent_logger import save_agent_status
            save_agent_status("launcher", "failed", {"error": str(e)})
        except:
            pass

    print("\n✅ GIWANOS 런처 실행 완료")

def run():
    main()

if __name__ == "__main__":
    main()
