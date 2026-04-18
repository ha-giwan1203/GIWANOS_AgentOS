"""
Gemini 토론 클라이언트 — API 기반 멀티턴 대화
사용: python gemini_debate.py --topic "주제" --rounds 3
"""
import os, sys, json, argparse, datetime, pathlib, textwrap
import urllib.request, urllib.error

API_KEY_FILE = pathlib.Path.home() / ".gemini" / "api_key.env"
LOG_DIR = pathlib.Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def load_api_key() -> str:
    if "GEMINI_API_KEY" in os.environ and os.environ["GEMINI_API_KEY"]:
        return os.environ["GEMINI_API_KEY"]
    if API_KEY_FILE.exists():
        for line in API_KEY_FILE.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("GEMINI_API_KEY 없음. ~/.gemini/api_key.env 확인")


def call_gemini(history: list, api_key: str) -> str:
    payload = json.dumps({"contents": history}).encode()
    req = urllib.request.Request(
        f"{GEMINI_URL}?key={api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        data = json.loads(e.read())
        raise RuntimeError(f"Gemini API 오류: {data.get('error', data)}")

    cands = data.get("candidates", [])
    if not cands:
        raise RuntimeError(f"응답 없음: {data}")
    parts = cands[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def harness_analyze(gemini_text: str) -> dict:
    """GPT 응답 하네스 분석: 주장 분해 → 라벨링 → 채택/보류/버림"""
    lines = [l.strip() for l in gemini_text.split("\n") if l.strip()]
    # 실제 NLP 없이 구조 템플릿만 반환 (Claude가 채워넣음)
    return {
        "raw": gemini_text,
        "note": "Claude가 직접 하네스 분석 수행 필요 (아래 출력 참조)",
    }


def save_log(topic: str, rounds: list, filename: str | None = None) -> pathlib.Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = filename or f"debate_{ts}.jsonl"
    path = LOG_DIR / fname
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"topic": topic, "model": GEMINI_MODEL, "ts": ts}, ensure_ascii=False) + "\n")
        for r in rounds:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def run_debate(topic: str, opening: str, max_rounds: int = 3) -> None:
    api_key = load_api_key()
    history = []
    rounds = []

    system_prompt = textwrap.dedent(f"""
        너는 전문 토론자다. 주제: {topic}
        - 한국어로만 답한다
        - 주장은 구체적 근거와 함께 제시한다
        - 상대 주장에서 동의할 수 있는 부분도 인정하되, 핵심 이견은 명확히 밝힌다
        - 답변은 200~400자 이내로 간결하게
    """).strip()

    # 첫 메시지: 시스템 + Claude 오프닝
    history.append({"role": "user", "parts": [{"text": f"[시스템]\n{system_prompt}\n\n[Claude 입장]\n{opening}"}]})

    print(f"\n{'='*60}")
    print(f"[토론 주제] {topic}")
    print(f"[모델] {GEMINI_MODEL}")
    print(f"{'='*60}")
    print(f"\n[Claude 오프닝]\n{opening}\n")

    for rnd in range(1, max_rounds + 1):
        print(f"\n--- Round {rnd} ---")
        gemini_resp = call_gemini(history, api_key)
        print(f"[Gemini]\n{gemini_resp}\n")

        rounds.append({"round": rnd, "role": "gemini", "text": gemini_resp})
        history.append({"role": "model", "parts": [{"text": gemini_resp}]})

        # Claude 반박은 사용자(Claude)가 직접 입력
        print("[Claude 반박 입력 (엔터 2번으로 확정, 'exit'로 종료)]: ")
        lines_buf = []
        while True:
            line = input()
            if line.lower() == "exit":
                break
            if line == "" and lines_buf and lines_buf[-1] == "":
                break
            lines_buf.append(line)

        claude_reply = "\n".join(lines_buf).strip()
        if not claude_reply or claude_reply.lower() == "exit":
            print("[토론 종료]")
            break

        rounds.append({"round": rnd, "role": "claude", "text": claude_reply})
        history.append({"role": "user", "parts": [{"text": claude_reply}]})
        print(f"[Claude]\n{claude_reply}\n")

    log_path = save_log(topic, rounds)
    print(f"\n[로그 저장] {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--opening", default="")
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()

    opening = args.opening or input("Claude 오프닝 입장을 입력하세요:\n> ")
    run_debate(args.topic, opening, args.rounds)
