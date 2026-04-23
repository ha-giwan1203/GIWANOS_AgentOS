"""
Gemini 토론 클라이언트 — API 기반 (멀티턴 + β안-C 단발 검증)

경로:
- 멀티턴: `call_gemini(history, api_key)` — 기존 CLI 토론용 (run_debate)
- β안-C 단발: `call_gemini_single(prompt, api_key, model)` — Step 6-2/6-4 교차 검증 전용
- β안-C 병렬: `call_gemini_parallel(prompts, api_key, model)` — OpenAI 병렬 호출과 동시 실행

β안-C 호출 규칙 (세션86 3자 만장일치 채택):
- 원문 payload 동봉 필수 — call_gemini_single(require_payload=True) 강제
- 본론(6-1, 6-3)·종합(6-5)·최종판정 API 호출 금지

사용:
  python gemini_debate.py --topic "주제" --rounds 3   # 멀티턴 CLI
  python -c "from gemini_debate import call_gemini_parallel; ..."
"""
import os, sys, json, argparse, datetime, pathlib, textwrap, concurrent.futures
import urllib.request, urllib.error

API_KEY_FILE = pathlib.Path.home() / ".gemini" / "api_key.env"
LOG_DIR = pathlib.Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
PAYLOAD_MIN_LEN = 40  # β안-C 원문 동봉 강제 임계


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


def _gemini_url_for(model: str) -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def call_gemini_single(prompt: str, api_key: str, model: str = GEMINI_MODEL,
                       system: str = "", max_tokens: int = 2000,
                       require_payload: bool = False) -> dict:
    """β안-C 단발 호출. history 없이 1턴. 원문 payload 강제 옵션.

    반환: {"text": str, "model": str, "finish_reason": str|None, "usage": dict}
    """
    if require_payload and len(prompt.strip()) < PAYLOAD_MIN_LEN:
        raise ValueError(
            f"payload 원문 동봉 필수 (β안-C) — 현재 길이 {len(prompt.strip())} < {PAYLOAD_MIN_LEN}. "
            "검증 대상 원문 전체를 payload에 포함해야 함 (요약·발췌·절삭 금지)."
        )
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": f"[시스템]\n{system}"}]})
        contents.append({"role": "model", "parts": [{"text": "이해."}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    req = urllib.request.Request(
        f"{_gemini_url_for(model)}?key={api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {e.code}: {err_body}")

    cands = data.get("candidates", [])
    if not cands:
        raise RuntimeError(f"응답 없음: {data}")
    parts = cands[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    return {
        "text": text,
        "model": data.get("modelVersion", model),
        "finish_reason": cands[0].get("finishReason"),
        "usage": data.get("usageMetadata", {}),
    }


def call_gemini_parallel(prompts: list, api_key: str, model: str = GEMINI_MODEL,
                         system: str = "", max_tokens: int = 2000) -> list:
    """β안-C 병렬 호출.

    prompts: [{"label": "gemini_verifies_gpt", "prompt": "..."}, ...]
    반환: [{"label": ..., "ok": bool, "result" or "error": ..., "model_id": ...}, ...]
    """
    results = [None] * len(prompts)

    def _worker(idx: int, item: dict) -> None:
        label = item.get("label", f"idx{idx}")
        p_text = item.get("prompt", "")
        try:
            r = call_gemini_single(p_text, api_key, model=model, system=system,
                                   max_tokens=max_tokens, require_payload=True)
            results[idx] = {
                "label": label,
                "ok": True,
                "result": r,
                "model_id": r.get("model", model),
            }
        except Exception as e:
            results[idx] = {
                "label": label,
                "ok": False,
                "error": str(e),
                "model_id": model,
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(prompts))) as ex:
        futures = [ex.submit(_worker, i, item) for i, item in enumerate(prompts)]
        concurrent.futures.wait(futures)
    return results


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
