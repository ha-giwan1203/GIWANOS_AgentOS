# 🕒 GIWANOS 주간 자동 회고 실행 계획

- 실행 대상: `auto_loop_discovery_runner.py`
- 주기: 매주 월요일 오전 9시
- 방식:
  - Windows: 작업 스케줄러에서 `.bat` 파일 등록
  - Linux/Mac: crontab 등록 예시:
    ```cron
    0 9 * * 1 cd /your/giwanos/path && python auto_loop_discovery_runner.py
    ```

- 로그 경로: `/logs/loop_run_history.json` 자동 축적 예정
- 회고 PDF → Slack / Notion 자동 전송 포함

