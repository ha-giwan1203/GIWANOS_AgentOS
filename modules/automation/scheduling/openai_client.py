"""OpenAI Client with cost optimisation"""
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic
import os, json, hashlib, datetime, pathlib, tiktoken, openai

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / "vector_cache" / "cache_responses.json"
CACHE.parent.mkdir(parents=True, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
ENC = tiktoken.encoding_for_model("gpt-3.5-turbo")

def _hash(txt:str)->str: return hashlib.sha256(txt.encode()).hexdigest()
def _cache_load():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {}
def _cache_save(obj): CACHE.write_text(json.dumps(obj, ensure_ascii=False))

def call(prompt:str, *, complexity:str="low", **kw)->str:
    cache=_cache_load(); h=_hash(prompt)
    if h in cache and (now_utc()-datetime.datetime.fromisoformat(cache[h]['ts'])).total_seconds()<86400:
        return cache[h]['resp']
    model="gpt-4o-turbo" if complexity=="high" else "gpt-3.5-turbo-0125"
    toks=ENC.encode(prompt); max_tok=16000
    if len(toks)>max_tok: prompt=ENC.decode(toks[-max_tok:])
    resp=openai.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}],temperature=0.3).choices[0].message.content.strip()
    cache[h]={"resp":resp,"ts":now_utc().isoformat()}; _cache_save(cache); return resp



