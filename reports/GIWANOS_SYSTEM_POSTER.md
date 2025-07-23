# 🧠 GIWANOS 시스템 구조 요약 포스터

## 🔁 루프 흐름 요약
설치 → 판단 → 실행 → 회고 → 예측 → 업그레이드 → 폐기 → 리포트

## 📂 주요 루프
- 판단: `judge_agent.py`
- 회고: `run_ai_reflection_full_loop.py`
- 리포트: `loop_leaderboard_report.py`, `loop_pattern_report.py`
- 복원: `loop_snapshot_loader.py`
- 폐기: `loop_retirement_checker.py`, `loop_retirement_archiver.py`

## 📦 설치 구성
- `.env.template` + `giwanos_setup.py`
- `giwanos_launcher.bat`
- `/logs/`, `/loop_agents/`, `/snapshots/`, `/reports/`

## 📱 모바일 전용 루프
- `loop_chat_interface.py`
- `loop_recommender_ai.py`
- `loop_reflection_writer_ai.py`
- `response_agent.py`

## 🧑 사용자/라인 분기
- `loop_user_profiles.json` + `loop_multi_user_router.py`

## 📊 시각화/보고
- Streamlit: `loop_dashboard_streamlit.py`
- 리더보드: `loop_leaderboard_report.py`
- 회고 PDF: `loop_reflection_ai_to_pdf.py`

## 🚨 알림/전송
- Slack: `loop_alert_dispatcher.py`
- 이메일: (선택) `loop_report_mailer.py`

## 🧠 설계 철학
- 모든 루프는 판단 가능한 단위로 구분되어 있고,
- 회고와 판단은 문서화되고 복원 가능하며,
- 운영체계는 기억과 함께 계속 진화한다.
