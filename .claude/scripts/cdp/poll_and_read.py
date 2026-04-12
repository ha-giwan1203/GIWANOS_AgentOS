"""GPT 응답 완료까지 polling 후 마지막 assistant 메시지 읽기."""
import sys, time
sys.path.insert(0, __file__.rsplit('\\', 1)[0] if '\\' in __file__ else __file__.rsplit('/', 1)[0])
from cdp_common import base_parser, connect_and_pick, cleanup

STOP_BTN_JS = '() => !!document.querySelector("[data-testid=\\"stop-button\\"]")'
READ_LAST_JS = """() => {
    const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
    if (msgs.length < 1) return 'NO MESSAGES';
    return msgs[msgs.length - 1].innerText;
}"""

def main():
    parser = base_parser("Poll GPT response and read")
    parser.add_argument("--max-wait", type=int, default=300, help="Max wait seconds")
    args = parser.parse_args()
    if not args.match_url and not args.match_url_exact and not args.match_title and args.tab is None:
        args.match_url = "chatgpt.com"

    pw, browser, page = connect_and_pick(args)
    try:
        intervals = [3, 5, 8, 8, 8]
        idx = 0
        elapsed = 0
        generating_seen = False

        while elapsed < args.max_wait:
            stop = page.evaluate(STOP_BTN_JS)
            if stop:
                generating_seen = True
                print(f"[{elapsed}s] GPT generating...", file=sys.stderr)
            else:
                if generating_seen:
                    print(f"[{elapsed}s] GPT done.", file=sys.stderr)
                    time.sleep(2)  # brief settle
                    break
                else:
                    print(f"[{elapsed}s] Waiting for generation to start...", file=sys.stderr)

            wait = intervals[min(idx, len(intervals)-1)]
            time.sleep(wait)
            elapsed += wait
            idx += 1

        result = page.evaluate(READ_LAST_JS)
        print(result)
    finally:
        cleanup(pw)

if __name__ == "__main__":
    main()
