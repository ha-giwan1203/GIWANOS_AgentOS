# [ACTIVE] VELOS 운영 철학 선언문
# =========================================================
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:/giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
# ------------------------------------------------------------
# [ACTIVE] slack_home_fix.py
# - Slack App Home 무한 로딩 복구용 최소 핸들러
# - Socket Mode 사용 (외부 URL/서명비밀 불필요)
# ------------------------------------------------------------
import os
from datetime import datetime

from dotenv import load_dotenv

# Slack Bolt (pip install slack_bolt slack_sdk)
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from modules.report_paths import ROOT
ROOT = str(ROOT)
ENV = os.path.join(ROOT, "configs", ".env")
if not os.path.exists(ENV):
    print(f"[ERROR] .env 없음: {ENV}")
    raise SystemExit(1)
load_dotenv(ENV)

BOT = os.getenv("SLACK_BOT_TOKEN")
APP = os.getenv("SLACK_APP_TOKEN")  # xapp-... (connections:write)
if not BOT or not APP:
    print("[ERROR] SLACK_BOT_TOKEN / SLACK_APP_TOKEN 누락")
    raise SystemExit(1)

app = App(token=BOT)  # Socket Mode에선 signing_secret 불필요


# 앱 홈 열릴 때마다 간단한 뷰 게시
@app.event("app_home_opened")
def update_home(client, event, logger):
    user = event.get("user")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        client.views_publish(
            user_id=user,
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "*VELOS Bot Home*"},
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"상태: ✅ alive  | 업데이트: `{ts}`",
                            }
                        ],
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "최근 동작:\n• 보고서 업로드 테스트는 `/velos test` 명령으로 실행\n• 이 홈 화면은 `app_home_opened` 이벤트로 자동 갱신됩니다.",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Ping"},
                                "action_id": "ping_btn",
                                "value": "ping",
                            }
                        ],
                    },
                ],
            },
        )
        logger.info(f"Home published for {user}")
    except Exception as e:
        logger.error(f"views_publish 실패: {e}")


@app.action("ping_btn")
def ping_btn(ack, body, client):
    ack()
    user = body["user"]["id"]
    client.chat_postMessage(channel=user, text="pong 🏓")


if __name__ == "__main__":
    print("[INFO] Socket Mode 시작… (Ctrl+C로 종료)")
    SocketModeHandler(app, APP).start()
