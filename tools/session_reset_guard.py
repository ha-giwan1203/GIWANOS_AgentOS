import sys, re, subprocess, os

MIN_LEN = 300         # 이보다 짧으면 의심
MUST_KEYS = ["VELOS_ROOT","절대경로 금지","최소 수정","PR 브랜치"]

def needs_reinject(text):
    if len(text) < MIN_LEN: return True
    text_low = text.lower()
    miss = [k for k in MUST_KEYS if k.lower() not in text_low]
    return len(miss) >= 2

def rebuild_context_pack():
    subprocess.run(["python", r"C:\giwanos\tools\make_context_pack.py"], check=False)
    with open(r"C:\giwanos\docs\CONTEXT_PACK.md","r",encoding="utf-8") as f:
        return f.read()

def main():
    # stdin으로 GPT 응답을 받는다고 가정
    text = sys.stdin.read()
    if needs_reinject(text):
        cp = rebuild_context_pack()
        sys.stdout.write("<<CONTEXT_REINJECT>>\n")
        sys.stdout.write(cp)
        sys.stdout.write("\n\n")
        sys.stdout.write("<<ORIGINAL_REPLY>>\n")
        sys.stdout.write(text)
    else:
        sys.stdout.write(text)

if __name__ == "__main__":
    main()
