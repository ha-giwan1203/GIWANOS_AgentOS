# 🔍 반복 오류 분석 결과 (자동 감지)

다음 모듈에서 반복되는 오류가 감지되었습니다:

- `Traceback (most recent call last):`: 6회 발생
- `2025-07-27 21:23:32,965 [ERROR] Failed to import modules: cannot import name 'send_report_email' fro`: 1회 발생
- `2025-07-27 21:30:50,918 [ERROR] Module import failed: cannot import name 'send_report_email' from 'n`: 1회 발생
- `2025-07-27 21:38:40,818 [ERROR] Module import failed: cannot import name 'send_report_email' from 'n`: 1회 발생
- `2025-07-27 21:41:11,756 [ERROR] Module import failed: cannot import name 'send_test_email' from 'not`: 1회 발생
- `2025-07-27 21:43:23,976 [ERROR] Module import failed: cannot import name 'sync' from 'notion_integra`: 1회 발생
- `2025-07-27 23:03:04,166 [ERROR] 시스템 상태 로드 중 오류: [Errno 2] No such file or directory: 'C:/giwanos/dat`: 1회 발생
- `2025-07-28 00:17:40,014 [ERROR] 시스템 상태 로드 중 오류: [Errno 2] No such file or directory: 'C:/giwanos/dat`: 1회 발생
- `2025-07-28 00:41:56,491 [ERROR] Module import failed: cannot import name 'sync' from 'notion_integra`: 1회 발생
- `2025-07-28 01:25:52,989 [ERROR] 시스템 상태 로드 중 오류: [Errno 2] No such file or directory: 'C:/giwanos/dat`: 1회 발생

🚨 해당 모듈의 로직 점검 및 리팩터링을 권장합니다.