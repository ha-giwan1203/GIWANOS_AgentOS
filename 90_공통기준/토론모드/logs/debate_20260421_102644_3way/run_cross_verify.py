"""
β안-C 단발 교차 검증 병렬 실행 러너 (세션86 Notion 의제 Round 1)

- 6-2: Gemini API → GPT 원문 판정
- 6-4: OpenAI API → Gemini 원문 판정
- 병렬 실행, 실패 시 1회 재시도 + fallback 플래그
- JSON + MD 이중 기록
"""
from __future__ import annotations

import json
import pathlib
import sys
import concurrent.futures

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]  # 업무리스트
sys.path.insert(0, str(REPO_ROOT / "90_공통기준" / "토론모드"))

from openai.openai_debate import call_openai, load_api_key as load_openai_key  # noqa: E402
from gemini.gemini_debate import call_gemini_single, load_api_key as load_gemini_key  # noqa: E402
from bridge.log_bridge import write_cross_verification  # noqa: E402
from bridge.api_fallback import run_with_fallback  # noqa: E402

GPT_TEXT = (HERE / "round1_gpt.md").read_text(encoding="utf-8").split("## 원문", 1)[1].split("## 하네스", 1)[0].strip()
GEMINI_TEXT = (HERE / "round1_gemini.md").read_text(encoding="utf-8").split("## 원문", 1)[1].split("## 하네스", 1)[0].strip()

SYSTEM_VERIFY = (
    "당신은 3자 토론 교차검증자다. 제시된 상대 모델 원문에 대해 "
    "'동의' / '이의' / '검증 필요' 중 하나로 1줄 판정하고, "
    "근거를 1문장으로 제시한다. 출력 형식은 정확히 다음 JSON:\n"
    '{"verdict":"동의|이의|검증 필요","reason":"..."}'
)

GEMINI_VERIFIES_GPT_PROMPT = f"""다음 GPT 본론 응답에 대해 1줄 검증 요청.

의제: Notion 동기화 정상화 (A/B/C 복구안 중 적합안 판정 + 부가 조건)

[GPT 원문 전체]
{GPT_TEXT}

응답 형식: 위 시스템 지시대로 JSON 한 줄만."""

GPT_VERIFIES_GEMINI_PROMPT = f"""다음 Gemini 본론 응답에 대해 1줄 검증 요청.

의제: Notion 동기화 정상화 (A/B/C 복구안 중 적합안 판정 + 부가 조건)

[Gemini 원문 전체]
{GEMINI_TEXT}

응답 형식: 위 시스템 지시대로 JSON 한 줄만."""


def parse_verdict_json(text: str) -> dict:
    """LLM이 반환한 JSON 1줄 파싱. 코드블록·여분 문자 허용."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`").lstrip("json").strip()
    # 첫 { 부터 마지막 } 까지
    start = t.find("{")
    end = t.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"JSON 블록 미발견: {text!r}")
    return json.loads(t[start : end + 1])


def task_gemini_verifies_gpt():
    key = load_gemini_key()
    r = call_gemini_single(
        GEMINI_VERIFIES_GPT_PROMPT,
        key,
        system=SYSTEM_VERIFY,
        max_tokens=2000,
        require_payload=True,
    )
    parsed = parse_verdict_json(r["text"])
    return {
        "verdict": parsed["verdict"],
        "reason": parsed["reason"],
        "model_id": r.get("model", "gemini-2.5-flash"),
    }


def task_gpt_verifies_gemini():
    key = load_openai_key()
    r = call_openai(
        GPT_VERIFIES_GEMINI_PROMPT,
        key,
        system=SYSTEM_VERIFY,
        max_tokens=500,
        temperature=0.2,
        require_payload=True,
    )
    parsed = parse_verdict_json(r["text"])
    return {
        "verdict": parsed["verdict"],
        "reason": parsed["reason"],
        "model_id": r.get("model", "gpt-4o"),
    }


def main() -> int:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fg = ex.submit(lambda: run_with_fallback(task_gemini_verifies_gpt, max_retry=1))
        fo = ex.submit(lambda: run_with_fallback(task_gpt_verifies_gemini, max_retry=1))
        rg = fg.result()
        ro = fo.result()

    print("[6-2 Gemini→GPT]", json.dumps(rg, ensure_ascii=False, indent=2))
    print("[6-4 GPT→Gemini]", json.dumps(ro, ensure_ascii=False, indent=2))

    if rg.get("fallback_required") or ro.get("fallback_required"):
        print("\n[FALLBACK] API 실패 — 웹 UI 경로 복귀 필요", file=sys.stderr)
        return 2

    gemini_verifies_gpt = rg["result"]
    gpt_verifies_gemini = ro["result"]

    json_path, md_path = write_cross_verification(
        round_n=1,
        gemini_verifies_gpt=gemini_verifies_gpt,
        gpt_verifies_gemini=gpt_verifies_gemini,
        log_dir=str(HERE),
    )
    print(f"\n[LOG] json={json_path}\n[LOG] md={md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
