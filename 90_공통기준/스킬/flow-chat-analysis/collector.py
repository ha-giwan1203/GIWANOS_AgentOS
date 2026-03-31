"""
Flow.team SP3S03 채팅방 메시지 수집기 (Playwright 기반)

사용법:
  1. 최초 1회 (로컬 Windows에서 실행):
     login.bat 더블클릭 또는 python collector.py --login
     → 전용 브라우저 열림 → Flow.team 로그인 → Enter
     → 전용 프로필에 세션 저장됨

  2. 수집 (headless 가능):
     collect.bat 더블클릭 또는 python collector.py
     → 저장된 프로필로 headless 접속 → 채팅 메시지 수집

  3. 특정 채팅방:
     python collector.py --room 2938379

출력:
  - output/messages_raw.json: 수집된 원시 메시지
  - output/messages.csv: 정규화된 CSV (분류 스킬 입력용)
  - output/network_debug.json: 네트워크 응답 디버그 정보
"""

import argparse
import json
import csv
import re
import hashlib
import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright 미설치. 설치: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

# 설정
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
# 영문 경로 (한글 경로 spawn 에러 방지)
PROFILE_DIR = Path.home() / ".flow-collector-profile"
FLOW_URL = "https://flow.team"
DEFAULT_ROOM_SRNO = "2938379"  # SP3S03 운영


def login_mode():
    """최초 로그인 — 사용자가 전용 브라우저에서 직접 로그인"""
    print("[LOGIN] 전용 브라우저를 엽니다. Flow.team에 로그인해주세요.")
    print("[LOGIN] 로그인 완료 후 이 터미널에서 Enter를 누르세요.")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1400, "height": 900},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(f"{FLOW_URL}/l/dashboard")

        input("[LOGIN] 로그인 완료 후 Enter...")
        browser.close()

    print(f"[LOGIN] 프로필 저장 완료: {PROFILE_DIR}")
    print("[LOGIN] 이제 'python collector.py' 또는 collect.bat으로 수집 가능")


def _make_dedupe_key(text: str) -> str:
    """메시지 텍스트 기반 중복 제거 키 생성 (좌표 무시)"""
    normalized = re.sub(r'\s+', ' ', text.strip())[:200]
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def collect_messages(room_srno: str, max_scroll: int = 200):
    """채팅 메시지 수집 — headless 모드"""

    if not PROFILE_DIR.exists():
        print("[ERROR] 로그인 프로필 없음. login.bat 또는 'python collector.py --login' 먼저 실행")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    seen_keys = set()
    messages = []
    network_debug = []    # URL/status/keys 디버그
    network_items = []    # 실제 메시지 후보

    with sync_playwright() as p:
        # headless로 수집 (GUI 없이)
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=True,
            viewport={"width": 1400, "height": 900},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()

        # 네트워크 응답 가로채기
        def handle_response(response):
            url = response.url
            if any(kw in url for kw in ["CHAT", "MSG", "COLABO"]):
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        network_debug.append({
                            "url": url[:200],
                            "status": response.status,
                            "keys": list(body.keys())[:15],
                        })
                        # 메시지 배열 탐색
                        for key in body:
                            val = body[key]
                            if isinstance(val, list) and len(val) > 0:
                                first = val[0]
                                if isinstance(first, dict) and any(
                                    k in first for k in ["MSG_CONTS", "CONTS", "msg", "content", "text",
                                                          "CHAT_CONTS", "SENDER_NM", "SEND_DTTM"]
                                ):
                                    for item in val:
                                        network_items.append(item)
                except Exception:
                    pass

        page.on("response", handle_response)

        # SP3S03 프로젝트 페이지로 직접 이동 (room 지정)
        print(f"[COLLECT] Flow.team SP3S03 프로젝트 접속 중...")
        page.goto(f"{FLOW_URL}/main.act?detail")
        page.wait_for_load_state("networkidle")

        # 채팅 팝업 열기
        print(f"[COLLECT] 채팅방 {room_srno} 팝업 열기...")
        try:
            with page.expect_popup(timeout=15000) as popup_info:
                # data-focus-room-srno에서 roomSrno 확인 후 채팅 버튼 클릭
                page.evaluate("""() => {
                    const btn = document.querySelector('.js-project-chat.participant-button');
                    if (btn) btn.click();
                }""")
            popup = popup_info.value
            print(f"[COLLECT] 채팅 팝업 열림: {popup.url}")

            # 팝업 URL에서 room 확인
            if room_srno not in popup.url and room_srno not in page.url:
                print(f"[WARN] 팝업 URL에 room {room_srno} 미포함. 열린 방이 맞는지 확인 필요")

            popup.on("response", handle_response)
            popup.wait_for_load_state("networkidle")
            popup.wait_for_timeout(2000)

            # 스크롤 컨테이너 찾기
            print(f"[COLLECT] 스크롤 컨테이너 탐색...")
            scroll_selector = popup.evaluate("""() => {
                // 채팅 스크롤 컨테이너 후보 탐색
                const candidates = document.querySelectorAll('[class*="scroll"], [class*="chat-list"], [class*="msg-list"], [class*="chat-body"]');
                for (const el of candidates) {
                    if (el.scrollHeight > el.clientHeight && el.clientHeight > 100) {
                        return { found: true, class: el.className.substring(0, 80), scrollHeight: el.scrollHeight };
                    }
                }
                // fallback: 가장 큰 스크롤 영역
                let best = null;
                let bestHeight = 0;
                document.querySelectorAll('div').forEach(el => {
                    if (el.scrollHeight > el.clientHeight && el.clientHeight > 200 && el.scrollHeight > bestHeight) {
                        best = el;
                        bestHeight = el.scrollHeight;
                    }
                });
                if (best) return { found: true, class: best.className.substring(0, 80), scrollHeight: best.scrollHeight };
                return { found: false };
            }""")
            print(f"[COLLECT] 스크롤 컨테이너: {scroll_selector}")

            # 메시지 수집 루프
            print(f"[COLLECT] 메시지 수집 시작 (최대 {max_scroll}회 스크롤)...")
            prev_count = 0
            no_change_count = 0

            for i in range(max_scroll):
                current_messages = popup.evaluate("""() => {
                    const msgs = [];
                    const msgElements = document.querySelectorAll(
                        '[class*="chat-message"], [class*="msg-item"], [class*="chat-item"], ' +
                        '[class*="message-wrap"], [class*="chat-wrap"], [class*="chat-content"]'
                    );
                    for (const el of msgElements) {
                        const text = el.innerText || '';
                        if (text.trim() && text.length > 3) {
                            msgs.push({
                                html_class: el.className.substring(0, 100),
                                text: text.substring(0, 2000)
                            });
                        }
                    }
                    if (msgs.length === 0) {
                        document.querySelectorAll('div[class]').forEach(el => {
                            const cls = el.className || '';
                            if (cls.includes('chat') || cls.includes('msg') || cls.includes('message')) {
                                const text = el.innerText || '';
                                if (text.trim() && text.length > 5 && text.length < 5000) {
                                    msgs.push({ html_class: cls.substring(0, 100), text: text.substring(0, 2000) });
                                }
                            }
                        });
                    }
                    return msgs;
                }""")

                # 중복 제거 (텍스트 기반 hash)
                for msg in current_messages:
                    key = _make_dedupe_key(msg.get("text", ""))
                    if key not in seen_keys:
                        seen_keys.add(key)
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

                # 내부 스크롤 컨테이너 위로 스크롤
                popup.evaluate("""() => {
                    const containers = document.querySelectorAll('[class*="scroll"], [class*="chat-list"], [class*="msg-list"], [class*="chat-body"]');
                    for (const el of containers) {
                        if (el.scrollHeight > el.clientHeight && el.clientHeight > 100) {
                            el.scrollTop = 0;
                            return;
                        }
                    }
                    window.scrollTo(0, 0);
                }""")
                popup.wait_for_timeout(800)

            popup.close()

        except Exception as e:
            print(f"[WARN] 팝업 열기 실패: {e}")
            print("[WARN] login.bat으로 로그인 상태 확인 후 재시도")

        browser.close()

    # 결과 저장
    _save_results(room_srno, messages, network_debug, network_items)
    return messages


def _save_results(room_srno, messages, network_debug, network_items):
    """수집 결과 저장"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 원시 데이터
    raw_path = OUTPUT_DIR / "messages_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({
            "room_srno": room_srno,
            "collected_at": datetime.now().isoformat(),
            "dom_messages": messages,
            "network_items": network_items,
            "total_dom": len(messages),
            "total_network": len(network_items),
        }, f, ensure_ascii=False, indent=2)

    # 네트워크 디버그
    debug_path = OUTPUT_DIR / "network_debug.json"
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(network_debug, f, ensure_ascii=False, indent=2)

    # CSV 정규화
    csv_path = OUTPUT_DIR / "messages.csv"
    _normalize_to_csv(messages, room_srno, csv_path)

    print(f"[DONE] 원시: {raw_path} (DOM {len(messages)}건, Net {len(network_items)}건)")
    print(f"[DONE] 디버그: {debug_path}")
    print(f"[DONE] CSV: {csv_path}")


def _normalize_to_csv(messages, room_srno, csv_path):
    """DOM 메시지를 정규화 CSV로 변환 (author 포함)"""
    datetime_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})')
    time_pattern = re.compile(r'(오전|오후)\s*(\d{1,2}):(\d{2})')
    # 작성자 패턴: "이름_소속" 또는 "이름" (줄 시작)
    author_pattern = re.compile(r'^([가-힣a-zA-Z_]+(?:_[가-힣a-zA-Z]+)?)\s*$', re.MULTILINE)

    rows = []
    for msg in messages:
        text = msg.get("text", "")
        lines = text.strip().split('\n')

        # 날짜 추출
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

        # 작성자 추출 (첫 줄 또는 두번째 줄에서)
        author = ""
        for line in lines[:3]:
            am = author_pattern.match(line.strip())
            if am:
                author = am.group(1)
                break

        rows.append({
            "date": date_str,
            "time": time_str,
            "author": author,
            "text": text.strip()[:2000],
            "room_srno": room_srno,
            "source": "dom",
        })

    fieldnames = ["date", "time", "author", "text", "room_srno", "source"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DONE] CSV 저장: {csv_path} ({len(rows)}건)")


def main():
    parser = argparse.ArgumentParser(description="Flow.team 채팅 메시지 수집기")
    parser.add_argument("--login", action="store_true", help="최초 로그인 모드 (GUI)")
    parser.add_argument("--room", default=DEFAULT_ROOM_SRNO, help="채팅방 ID (기본: SP3S03)")
    parser.add_argument("--max-scroll", type=int, default=200, help="최대 스크롤 횟수")
    parser.add_argument("--headed", action="store_true", help="수집 시 GUI 브라우저 사용")
    args = parser.parse_args()

    if args.login:
        login_mode()
    else:
        collect_messages(args.room, args.max_scroll)


if __name__ == "__main__":
    main()
