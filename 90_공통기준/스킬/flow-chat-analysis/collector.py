"""
Flow.team SP3S03 채팅방 메시지 수집기 (CDP 연결 방식)

사용법:
  1. login.bat 실행 → Chrome이 디버깅 모드로 열림
  2. Flow.team에 카카오 계정으로 로그인
  3. collect.bat 실행 또는 python collector.py
     → 로그인된 Chrome에 CDP로 연결 → 채팅 메시지 수집

원리:
  - Playwright가 새 브라우저를 띄우지 않음
  - 이미 로그인된 Chrome에 connect_over_cdp()로 붙음
  - 카카오 봇 감지 우회 (로그인 자동화 안 함)

출력:
  - output/messages_raw.json: 수집된 원시 메시지
  - output/messages.csv: 정규화된 CSV (분류 스킬 입력용)
  - output/network_debug.json: 네트워크 응답 디버그
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

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
CDP_URL = "http://127.0.0.1:9222"
FLOW_URL = "https://flow.team"
DEFAULT_ROOM_SRNO = "2938379"


def _make_dedupe_key(text: str) -> str:
    normalized = re.sub(r'\s+', ' ', text.strip())[:200]
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def collect_messages(room_srno: str, max_scroll: int = 200):
    """CDP로 기존 Chrome에 연결하여 채팅 메시지 수집"""

    OUTPUT_DIR.mkdir(exist_ok=True)
    seen_keys = set()
    messages = []
    network_debug = []
    network_items = []

    with sync_playwright() as p:
        # CDP로 기존 Chrome에 연결
        print(f"[COLLECT] Chrome CDP 연결 시도: {CDP_URL}")
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"[ERROR] Chrome 연결 실패: {e}")
            print("[ERROR] login.bat으로 Chrome을 디버깅 모드로 먼저 실행하세요.")
            sys.exit(1)

        print(f"[COLLECT] Chrome 연결 성공. 컨텍스트 {len(browser.contexts)}개")

        # 기존 컨텍스트 사용
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        pages = context.pages
        print(f"[COLLECT] 열린 탭 {len(pages)}개")

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
                        for key in body:
                            val = body[key]
                            if isinstance(val, list) and len(val) > 0:
                                first = val[0]
                                if isinstance(first, dict) and any(
                                    k in first for k in ["MSG_CONTS", "CONTS", "content", "text",
                                                          "CHAT_CONTS", "SENDER_NM", "SEND_DTTM"]
                                ):
                                    for item in val:
                                        network_items.append(item)
                except Exception:
                    pass

        # 이미 열린 채팅 탭 찾기 또는 팝업 열기
        chat_page = None
        flow_page = None
        for pg in pages:
            if 'messenger.act' in pg.url:
                chat_page = pg
                print(f"[COLLECT] 채팅 탭 발견 (이미 열림): {pg.url}")
                break
            if 'flow.team' in pg.url:
                flow_page = pg

        if not chat_page and flow_page:
            # 채팅 탭이 없으면 팝업 열기 시도
            print(f"[COLLECT] 채팅방 {room_srno} 팝업 열기...")
            try:
                with flow_page.expect_popup(timeout=15000) as popup_info:
                    flow_page.evaluate("""() => {
                        const btn = document.querySelector('.js-project-chat.participant-button');
                        if (btn) btn.click();
                    }""")
                chat_page = popup_info.value
                print(f"[COLLECT] 채팅 팝업 열림: {chat_page.url}")
            except Exception as e:
                print(f"[ERROR] 팝업 열기 실패: {e}")
                print("[TIP] 디버깅 Chrome에서 채팅방을 직접 열어주세요.")
                browser.close()
                return messages

        if not chat_page:
            print("[ERROR] 채팅 탭을 찾을 수 없습니다. 디버깅 Chrome에서 채팅방을 열어주세요.")
            browser.close()
            return messages

        try:
            chat_page.on("response", handle_response)
            chat_page.wait_for_timeout(1000)

            # 스크롤 컨테이너 탐색
            scroll_info = chat_page.evaluate("""() => {
                const candidates = document.querySelectorAll('[class*="scroll"], [class*="chat-list"], [class*="msg-list"], [class*="chat-body"]');
                for (const el of candidates) {
                    if (el.scrollHeight > el.clientHeight && el.clientHeight > 100) {
                        return { found: true, cls: el.className.substring(0, 80), height: el.scrollHeight };
                    }
                }
                let best = null, bestH = 0;
                document.querySelectorAll('div').forEach(el => {
                    if (el.scrollHeight > el.clientHeight && el.clientHeight > 200 && el.scrollHeight > bestH) {
                        best = el; bestH = el.scrollHeight;
                    }
                });
                if (best) return { found: true, cls: best.className.substring(0, 80), height: best.scrollHeight };
                return { found: false };
            }""")
            print(f"[COLLECT] 스크롤 컨테이너: {scroll_info}")

            # 메시지 수집 루프
            print(f"[COLLECT] 메시지 수집 시작 (최대 {max_scroll}회 스크롤)...")
            prev_count = 0
            no_change = 0

            for i in range(max_scroll):
                current = chat_page.evaluate("""() => {
                    const msgs = [];
                    // chat-left clearfix = 개별 메시지 블록
                    const blocks = document.querySelectorAll('.chat-left.clearfix');
                    for (const block of blocks) {
                        // chat-txt = 메시지 본문 (깨끗한 텍스트)
                        const txtEl = block.querySelector('.chat-txt');
                        const text = txtEl ? txtEl.innerText.trim() : '';
                        if (!text || text.length < 3) continue;

                        // 작성자명 (chat-name 또는 이전 요소)
                        const nameEl = block.querySelector('.chat-name') || block.previousElementSibling?.querySelector?.('.chat-name');
                        const author = nameEl ? nameEl.innerText.trim() : '';

                        // 시간 (chat-btns 안)
                        const timeEl = block.querySelector('.chat-btns');
                        let time = '';
                        if (timeEl) {
                            const timeMatch = timeEl.innerText.match(/(오전|오후)\s*(\d{1,2}):(\d{2})/);
                            if (timeMatch) time = timeMatch[0];
                        }

                        msgs.push({ cls: 'chat-left', text, author, time });
                    }

                    // 날짜 구분선도 수집 (월별 분류용)
                    const dates = document.querySelectorAll('.chat-date');
                    for (const d of dates) {
                        msgs.push({ cls: 'chat-date', text: d.innerText.trim(), author: '', time: '' });
                    }

                    return msgs;
                }""")

                for msg in current:
                    key = _make_dedupe_key(msg.get("text", ""))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        messages.append(msg)

                cnt = len(messages)
                if cnt == prev_count:
                    no_change += 1
                    if no_change >= 5:
                        print(f"[COLLECT] 더 이상 새 메시지 없음. 총 {cnt}건")
                        break
                else:
                    no_change = 0
                    if i % 10 == 0:
                        print(f"[COLLECT] 스크롤 {i}/{max_scroll}, 메시지 {cnt}건")
                prev_count = cnt

                # 내부 스크롤 컨테이너 위로 스크롤
                chat_page.evaluate("""() => {
                    const els = document.querySelectorAll('[class*="scroll"], [class*="chat-list"], [class*="msg-list"], [class*="chat-body"]');
                    for (const el of els) {
                        if (el.scrollHeight > el.clientHeight && el.clientHeight > 100) {
                            el.scrollTop = 0;
                            return;
                        }
                    }
                    window.scrollTo(0, 0);
                }""")
                chat_page.wait_for_timeout(800)

            print(f"[COLLECT] 수집 완료.")

        except Exception as e:
            print(f"[ERROR] 팝업 열기/수집 실패: {e}")
            print("[TIP] Flow.team SP3S03 프로젝트 페이지가 열려있는지 확인하세요.")

        # CDP 연결 해제 (Chrome은 종료 안 됨)
        browser.close()

    _save_results(room_srno, messages, network_debug, network_items)
    return messages


def _save_results(room_srno, messages, network_debug, network_items):
    OUTPUT_DIR.mkdir(exist_ok=True)

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

    debug_path = OUTPUT_DIR / "network_debug.json"
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(network_debug, f, ensure_ascii=False, indent=2)

    csv_path = OUTPUT_DIR / "messages.csv"
    _normalize_to_csv(messages, room_srno, csv_path)

    print(f"[DONE] 원시: {raw_path} (DOM {len(messages)}건, Net {len(network_items)}건)")
    print(f"[DONE] CSV: {csv_path}")


def _normalize_to_csv(messages, room_srno, csv_path):
    datetime_pat = re.compile(r'(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})')
    time_pat = re.compile(r'(오전|오후)\s*(\d{1,2}):(\d{2})')
    author_pat = re.compile(r'^([가-힣a-zA-Z_]+(?:_[가-힣a-zA-Z]+)?)\s*$', re.MULTILINE)

    rows = []
    for msg in messages:
        text = msg.get("text", "")
        lines = text.strip().split('\n')

        dt = datetime_pat.search(text)
        tm = time_pat.search(text)
        date_str = dt.group(1) if dt else ""
        time_str = ""
        if dt:
            time_str = dt.group(2)
        elif tm:
            h = int(tm.group(2))
            m = tm.group(3)
            if tm.group(1) == "오후" and h != 12: h += 12
            elif tm.group(1) == "오전" and h == 12: h = 0
            time_str = f"{h:02d}:{m}"

        author = ""
        for line in lines[:3]:
            am = author_pat.match(line.strip())
            if am:
                author = am.group(1)
                break

        rows.append({
            "date": date_str, "time": time_str, "author": author,
            "text": text.strip()[:2000], "room_srno": room_srno, "source": "dom",
        })

    fields = ["date", "time", "author", "text", "room_srno", "source"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"[DONE] CSV: {csv_path} ({len(rows)}건)")


def main():
    parser = argparse.ArgumentParser(description="Flow.team 채팅 수집기 (CDP)")
    parser.add_argument("--room", default=DEFAULT_ROOM_SRNO, help="채팅방 ID")
    parser.add_argument("--max-scroll", type=int, default=200, help="최대 스크롤 횟수")
    parser.add_argument("--cdp-url", default=CDP_URL, help="Chrome CDP URL")
    args = parser.parse_args()

    collect_messages(args.room, args.max_scroll)


if __name__ == "__main__":
    main()
