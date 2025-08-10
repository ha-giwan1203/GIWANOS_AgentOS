import re
_PAT = [
    re.compile(r"\b010[- ]?\d{4}[- ]?\d{4}\b"),   # 휴대폰
    re.compile(r"(?:fuck|shit|bitch)", re.I),     # 욕설
]
def is_safe(t: str) -> bool: return not any(p.search(t) for p in _PAT)
def sanitize(t: str) -> str:
    for p in _PAT: t = p.sub("[REDACTED]", t)
    return t


