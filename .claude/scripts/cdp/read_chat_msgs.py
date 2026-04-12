"""ChatGPT 토론방에서 최근 assistant 메시지를 읽는 스크립트."""
import sys, argparse
sys.path.insert(0, __file__.rsplit('\\', 1)[0] if '\\' in __file__ else __file__.rsplit('/', 1)[0])
from cdp_common import base_parser, connect_and_pick, cleanup

JS_CODE = """() => {
    const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
    const texts = [];
    const count = Math.min(msgs.length, 5);
    for (let i = msgs.length - count; i < msgs.length; i++) {
        texts.push("=== MSG " + i + " ===\\n" + msgs[i].innerText.substring(0, 5000));
    }
    return texts.join("\\n\\n");
}"""

def main():
    parser = base_parser("Read ChatGPT assistant messages")
    parser.add_argument("--count", type=int, default=5, help="Number of recent messages to read")
    args = parser.parse_args()
    if not args.match_url and not args.match_url_exact and not args.match_title and args.tab is None:
        args.match_url = "chatgpt.com"

    pw, browser, page = connect_and_pick(args)
    try:
        result = page.evaluate(JS_CODE)
        print(result)
    finally:
        cleanup(pw)

if __name__ == "__main__":
    main()
