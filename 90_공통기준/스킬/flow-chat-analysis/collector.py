"""
Flow.team SP3S03 채팅방 메시지 수집기 (Playwright 기반)

사용법:
  1. 최초 1회: python collector.py --login
     → 전용 브라우저가 열림 → Flow.team 로그인 → 브라우저 닫기
     → 로그인 세션이 auth_state.json에 저장됨

  2. 수집: python collector.py
     → 저장된 세션으로 자동 접속 → 채팅 메시지 수집 → messages.json 저장

  3. 특정 채팅방: python collector.py --room 2938379

출력:
  - messages_raw.json: 수집된 원시 메시지 (날짜, 작성자, 본문)
  - messages.csv: 정규화된 CSV (분류 스킬 입력용)
"""

import argparse
import json
import csv
import re
import os
import sys
from pathlib import Path
from datetime import datetime

# Playwright import
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright가 설치되어 있지 않습니다.")
    print("설치: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

# 설정
SCRIPT_DIR = Path(__file__).parent
AUTH_STATE_FILE = SCRIPT_DIR / "auth_state.json"
OUTPUT_DIR = SCRIPT_DIR / "output"
FLOW_URL = "https://flow.team"
DEFAULT_ROOM_SRNO = "2938379"  # SP3S03 운영

# .gitignore에 민감 파일 추가
GITIGNORE_FILE = SCRIPT_DIR / ".gitignore"
GITIGNORE_CONTENT = """auth_state.json
output/
*.pyc
__pycache__/
"""


def ensure_gitignore():
    """민감 파일이 Git에 올라가지 않도록 .gitignore 생성"""
    if not GITIGNORE_FILE.exists():
        GITIGNORE_FILE.write_text(GITIGNORE_CONTENT, encoding="utf-8")
        print(f"[INFO] .gitignore 생성: {GITIGNORE_FILE}")


def login_mode():
    """최초 로그인 — 사용자가 직접 로그인하고 세션 저장"""
    print("[LOGIN] 전용 브라우저를 엽니다. Flow.team에 로그인해주세요.")
    print("[LOGIN] 로그인 완료 후 브라우저를 닫으면 세션이 저장됩니다.")

    with sync_playwright() as p:
        # 전용 프로필 디렉토리 사용
        user_data_dir = SCRIPT_DIR / "playwright_profile"
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1400, "height": 900},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(f"{FLOW_URL}/l/dashboard")

        print("[LOGIN] 로그인 후 이 터미널에서 Enter를 누르세요...")
        input()

        # 세션 저장
        browser.storage_state(path=str(AUTH_STATE_FILE))
        browser.close()

    print(f"[LOGIN] 세션 저장 완료: {AUTH_STATE_FILE}")
    print("[LOGIN] 이제 'python collector.py' 로 수집할 수 있습니다.")


def collect_messages(room_srno: str, max_scroll: int = 200):
    """채팅 메시지 수집"""

    if not AUTH_STATE_FILE.exists():
        print("[ERROR] 로그인 세션이 없습니다. 먼저 'python collector.py --login' 실행")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    messages = []
    network_messages = []

    with sync_playwright() as p:
        # 저장된 세션으로 브라우저 시작
        user_data_dir = SCRIPT_DIR / "playwright_profile"
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1400, "height": 900},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # 네트워크 응답 가로채기 — 메시지 관련 API 캡처
        def handle_response(response):
            url = response.url
            if any(kw in url for kw in ["CHAT", "MSG", "chat", "msg", "message"]):
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        network_messages.append({
                            "url": url,
                            "status": response.status,
                            "keys": list(body.keys())[:10],
                        })
                        # 메시지 배열이 있으면 저장
                        for key in body:
                            if isinstance(body[key], list) and len(body[key]) > 0:
                                first = body[key][0]
                                if isinstance(first, dict) and any(
                                    k in first for k in ["MSG_CONTS", "msg", "content", "text", "CONTS"]
                                ):
                                    for item in body[key]:
                                        network_messages.append(item)
                except Exception:
                    pass

        page.on("response", handle_response)

        # Flow.team 메인 페이지 접속
        print(f"[COLLECT] Flow.team 접속 중...")
        page.goto(f"{FLOW_URL}/l/dashboard")
        page.wait_for_load_state("networkidle")

        # 채팅 팝업 열기 시도
        print(f"[COLLECT] 채팅방 {room_srno} 팝업 열기...")

        # 채팅 버튼 클릭으로 팝업 열기
        popup_promise = page.wait_for_event("popup", timeout=10000)

        # JS로 채팅 버튼 클릭
        page.evaluate("""() => {
            const btn = document.querySelector('.js-project-chat.participant-button');
            if (btn) btn.click();
        }""")

        try:
            popup = popup_promise
            print(f"[COLLECT] 채팅 팝업 열림: {popup.url}")
            popup.on("response", handle_response)
            popup.wait_for_load_state("networkidle")

            # 채팅 메시지 DOM에서 추출
            print(f"[COLLECT] 메시지 수집 시작 (최대 {max_scroll}회 스크롤)...")

            prev_count = 0
            no_change_count = 0

            for i in range(max_scroll):
                # 현재 화면의 메시지 추출
                current_messages = popup.evaluate("""() => {
                    const msgs = [];
                    // Flow 채팅 메시지 DOM 구조 탐색
                    const msgElements = document.querySelectorAll(
                        '[class*="chat-message"], [class*="msg-item"], [class*="chat-item"], ' +
                        '[class*="message-wrap"], [class*="chat-wrap"]'
                    );

                    for (const el of msgElements) {
                        const text = el.innerText || '';
                        if (text.trim()) {
                            msgs.push({
                                html_class: el.className.substring(0, 100),
                                text: text.substring(0, 2000),
                                rect_y: el.getBoundingClientRect().y
                            });
                        }
                    }

                    // 더 넓은 범위로도 시도
                    if (msgs.length === 0) {
                        const allDivs = document.querySelectorAll('div[class]');
                        for (const el of allDivs) {
                            const cls = el.className || '';
                            if (cls.includes('chat') || cls.includes('msg') || cls.includes('message')) {
                                const text = el.innerText || '';
                                if (text.trim() && text.length > 5 && text.length < 5000) {
                                    msgs.push({
                                        html_class: cls.substring(0, 100),
                                        text: text.substring(0, 2000),
                                        rect_y: el.getBoundingClientRect().y
                                    });
                                }
                            }
                        }
                    }

                    return msgs;
                }""")

                # 새 메시지 추가
                for msg in current_messages:
                    if msg not in messages:
                        messages.append(msg)

                current_count = len(messages)
                if current_count == prev_count:
                    no_change_count += 1
                    if no_change_count >= 5:
                        print(f"[COLLECT] 더 이상 새 메시지 없음. 총 {current_count}건")
                        break
                else:
                    no_change_count = 0
                    if i % 10 == 0:
                        print(f"[COLLECT] 스크롤 {i}/{max_scroll}, 메시지 {current_count}건")

                prev_count = current_count

                # 위로 스크롤
                popup.evaluate("window.scrollTo(0, 0)")
                popup.wait_for_timeout(500)

            popup.close()

        except Exception as e:
            print(f"[WARN] 팝업 열기 실패: {e}")
            print("[WARN] 직접 채팅방을 열어주세요. 10초 대기...")
            page.wait_for_timeout(10000)

        browser.close()

    # 결과 저장
    raw_output = OUTPUT_DIR / "messages_raw.json"
    with open(raw_output, "w", encoding="utf-8") as f:
        json.dump({
            "room_srno": room_srno,
            "collected_at": datetime.now().isoformat(),
            "dom_messages": messages,
            "network_captures": network_messages,
            "total_dom": len(messages),
            "total_network": len(network_messages),
        }, f, ensure_ascii=False, indent=2)

    print(f"[DONE] 원시 데이터 저장: {raw_output}")
    print(f"[DONE] DOM 메시지: {len(messages)}건, 네트워크 캡처: {len(network_messages)}건")

    # CSV 변환 (정규화)
    csv_output = OUTPUT_DIR / "messages.csv"
    normalize_to_csv(messages, csv_output)

    return messages, network_messages


def normalize_to_csv(messages, csv_path):
    """DOM 추출 메시지를 정규화된 CSV로 변환"""

    # 날짜/시간 패턴
    datetime_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})')
    time_pattern = re.compile(r'(오전|오후)\s*(\d{1,2}):(\d{2})')

    rows = []
    for msg in messages:
        text = msg.get("text", "")

        # 날짜 추출 시도
        dt_match = datetime_pattern.search(text)
        time_match = time_pattern.search(text)

        date_str = dt_match.group(1) if dt_match else ""
        time_str = ""
        if dt_match:
            time_str = dt_match.group(2)
        elif time_match:
            hour = int(time_match.group(2))
            minute = time_match.group(3)
            if time_match.group(1) == "오후" and hour != 12:
                hour += 12
            elif time_match.group(1) == "오전" and hour == 12:
                hour = 0
            time_str = f"{hour:02d}:{minute}"

        rows.append({
            "date": date_str,
            "time": time_str,
            "text": text.strip()[:2000],
            "source": "dom",
        })

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "time", "text", "source"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DONE] CSV 저장: {csv_path} ({len(rows)}건)")


def main():
    parser = argparse.ArgumentParser(description="Flow.team 채팅 메시지 수집기")
    parser.add_argument("--login", action="store_true", help="최초 로그인 모드")
    parser.add_argument("--room", default=DEFAULT_ROOM_SRNO, help="채팅방 ID (기본: SP3S03)")
    parser.add_argument("--max-scroll", type=int, default=200, help="최대 스크롤 횟수")
    args = parser.parse_args()

    ensure_gitignore()

    if args.login:
        login_mode()
    else:
        collect_messages(args.room, args.max_scroll)


if __name__ == "__main__":
    main()
