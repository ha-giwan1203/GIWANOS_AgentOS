"""
β안-C API 실패 fallback — 1회 재시도 후 웹 UI 복귀 플래그 반환.

규칙 (세션86 [NEVER] 6번):
- API 실패 시 1회 재시도만 허용. 무한 재시도 금지.
- 실패 지속 시 fallback_required=True 반환 — 호출자는 즉시 웹 UI 경로(gpt-send/gemini-send)로 복귀.
- rate limit(HTTP 429)은 즉시 fallback (재시도 안 함) — 예산·쿼터 보호.

사용:
  from bridge.api_fallback import run_with_fallback
  r = run_with_fallback(lambda: call_openai_parallel(prompts, key), max_retry=1)
  if r["fallback_required"]:
      # 웹 UI 경로로 복귀
      ...
"""
import time
import urllib.error
from typing import Callable, Any


def _is_rate_limit(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError) and getattr(exc, "code", 0) == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "quota" in msg


def run_with_fallback(
    action: Callable[[], Any],
    *,
    max_retry: int = 1,
    retry_delay_sec: float = 1.0,
) -> dict:
    """action 실행 → 실패 시 최대 max_retry 재시도 → 실패 지속 시 fallback 플래그.

    반환:
      {
        "ok": bool,
        "result": Any | None,
        "error": str | None,
        "fallback_required": bool,
        "attempts": int,
        "rate_limited": bool,
      }
    """
    if max_retry < 0:
        raise ValueError("max_retry must be >= 0")
    attempts = 0
    last_exc = None
    rate_limited = False

    for attempt in range(max_retry + 1):
        attempts += 1
        try:
            result = action()
            return {
                "ok": True,
                "result": result,
                "error": None,
                "fallback_required": False,
                "attempts": attempts,
                "rate_limited": False,
            }
        except Exception as e:
            last_exc = e
            if _is_rate_limit(e):
                rate_limited = True
                break  # rate limit은 재시도 무의미 — 즉시 fallback
            if attempt < max_retry:
                time.sleep(retry_delay_sec)
            else:
                break

    return {
        "ok": False,
        "result": None,
        "error": str(last_exc) if last_exc else "unknown",
        "fallback_required": True,
        "attempts": attempts,
        "rate_limited": rate_limited,
    }


def _self_test() -> int:
    """CLI --self-test. smoke_test 섹션 50-3에서 호출."""
    ok = True

    # 1) 성공 경로
    r = run_with_fallback(lambda: {"x": 1})
    if not r["ok"] or r["fallback_required"] or r["attempts"] != 1:
        print(f"[FAIL] happy path: {r}")
        ok = False

    # 2) 재시도 후 실패 → fallback
    counter = {"n": 0}
    def _always_fail():
        counter["n"] += 1
        raise RuntimeError("boom")
    r = run_with_fallback(_always_fail, max_retry=1, retry_delay_sec=0)
    if r["ok"] or not r["fallback_required"] or r["attempts"] != 2 or r["rate_limited"]:
        print(f"[FAIL] fallback path: {r} counter={counter}")
        ok = False

    # 3) 첫 번째 실패, 두 번째 성공 → ok=True
    counter = {"n": 0}
    def _fail_then_ok():
        counter["n"] += 1
        if counter["n"] == 1:
            raise RuntimeError("transient")
        return "recovered"
    r = run_with_fallback(_fail_then_ok, max_retry=1, retry_delay_sec=0)
    if not r["ok"] or r["fallback_required"] or r["result"] != "recovered" or r["attempts"] != 2:
        print(f"[FAIL] retry recovery: {r}")
        ok = False

    # 4) rate limit → 즉시 fallback, 재시도 없음
    counter = {"n": 0}
    def _rate_limited():
        counter["n"] += 1
        raise RuntimeError("HTTP 429 rate limit exceeded")
    r = run_with_fallback(_rate_limited, max_retry=3, retry_delay_sec=0)
    if r["ok"] or not r["fallback_required"] or not r["rate_limited"] or r["attempts"] != 1:
        print(f"[FAIL] rate limit fast-fail: {r}")
        ok = False

    if ok:
        print("[PASS] api_fallback self-test 4/4")
        return 0
    return 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(_self_test())
    print("usage: python api_fallback.py --self-test")
    sys.exit(2)
