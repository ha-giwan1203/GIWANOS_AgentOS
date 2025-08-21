# [EXPERIMENT] VELOS 벡터 검색 - 벡터 기반 검색 모듈
# [EXPERIMENT] VELOS 벡터 검색 - 벡터 기반 검색 모듈
# -*- coding: utf-8 -*-
import os
from pathlib import Path

import pandas as pd

from . import __dict__ as _dummy


def embed_search(query: str, topk=10, days=7):
    from modules.logs.indexer import load_conversations

    df = load_conversations(days=days, limit=5000, role=None, query=None)
    m = df[df["content"].str.contains(query, case=False, na=False)].head(topk)
    return m[["time", "role", "session", "content"]]
