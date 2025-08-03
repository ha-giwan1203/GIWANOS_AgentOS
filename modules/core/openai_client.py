"""VELOS OpenAI 비용 최적화 래퍼"""
import os, json, hashlib, datetime, pathlib, tiktoken, openai

BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
CACHE = BASE_DIR / "vector_cache" / "cache_responses.json"
CACHE.parent.mkdir(parents=True, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
ENC = tiktoken.encoding_for_model("gpt-3.5-turbo")

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def _load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}

def _save_cache(data: dict):
    CACHE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

def optimized_call(prompt: str, *, complexity: str = "low", **kwargs) -> str:
    """Return LLM response with caching & model tiering.
    complexity='low' → gpt-3.5-turbo-0125
    complexity='high' → gpt-4o-turbo
    """
    cache = _load_cache()
    key = _hash(prompt)
    if key in cache and (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(cache[key]['ts'])).total_seconds() < 86_400:
        return cache[key]['resp']

    model = "gpt-4o-turbo" if complexity == "high" else "gpt-3.5-turbo-0125"

    # truncate to last 16k tokens
    max_tokens = 16_000
    tokens = ENC.encode(prompt)
    if len(tokens) > max_tokens:
        prompt = ENC.decode(tokens[-max_tokens:])

    resp = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        **kwargs
    ).choices[0].message.content.strip()

    cache[key] = {"resp": resp, "ts": datetime.datetime.utcnow().isoformat()}
    _save_cache(cache)
    return resp
