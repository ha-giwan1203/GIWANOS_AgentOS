#!/usr/bin/env python
import os
import datetime
import traceback

print("💡 메모리 상태 점검 자동 실행 시작")

try:
    from memory_health_check_all import run_memory_check

    # 현재 주차 기준 파일명 설정
    today = datetime.date.today()
    year, week, _ = today.isocalendar()
    log_filename = f"logs/memory_status_{year}W{week:02}.json"

    # 메모리 점검 실행 및 결과 저장
    result = run_memory_check()
    os.makedirs("logs", exist_ok=True)
    with open(log_filename, "w", encoding="utf-8") as f:
        import json
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ 메모리 상태 점검 완료")

    # 향후 이메일 알림 처리 (예: 심각도 >= warning 시)
    # if result.get("status") == "warning":
    #     from send_alert_email import send_email
    #     send_email(subject="[경고] GIWANOS 메모리 상태 이상", body=json.dumps(result, indent=2))

except Exception as e:
    print("❌ 메모리 점검 중 오류 발생:")
    traceback.print_exc()

print("\n✅ 스크립트 종료")
