# -*- coding: utf-8 -*-
import re

RULES = [
    ("오류", re.compile(r"\b(ERROR|Exception|Traceback)\b", re.I)),
    ("욕설", re.compile(r"(씨발|개새끼|좆|병신)")),
    ("성능", re.compile(r"(느리|지연|성능|속도)")),
    ("보안", re.compile(r"(토큰|비밀번호|암호|secret)", re.I)),
]


def auto_tags(text: str):
    tags = [name for name, pat in RULES if pat.search(text or "")]
    return tags
