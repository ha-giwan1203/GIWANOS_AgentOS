# safe sitecustomize: just import guard; no monkeypatch here
import contextlib

with contextlib.suppress(Exception):
    pass
