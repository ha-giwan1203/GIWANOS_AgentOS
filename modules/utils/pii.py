# -*- coding: utf-8 -*-
import re

PAT_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PAT_PHONE = re.compile(r"\b(01[0-9]-?\d{3,4}-?\d{4})\b")
PAT_ID = re.compile(r"\b([A-Za-z][A-Za-z0-9_]{3,15})\b")


def scrub_text(t: str) -> str:
    if not t:
        return t
    t = PAT_EMAIL.sub("[email]", t)
    t = PAT_PHONE.sub("[phone]", t)
    return t
