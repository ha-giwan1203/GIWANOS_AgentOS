"""
β안-C 로그 브릿지 — Step 6-2/6-4 단발 교차 검증 결과를 Claude 6-5 종합 프롬프트로 원문 주입.

세션86 [3way] 만장일치 채택 (세션85 debate_20260420_190020_beta_3way Round 1).
상세: `../CLAUDE.md` "β안-C 예외", `../debate-mode/SKILL.md` Step 6-2/6-4 β안-C 섹션.

JSON 스키마 (SKILL.md:172-176 필수):
{
  "cross_verification": {
    "gemini_verifies_gpt": {"verdict": "동의|이의|검증 필요", "reason": "...", "model_id": "..."},
    "gpt_verifies_gemini": {"verdict": "동의|이의|검증 필요", "reason": "...", "model_id": "..."},
    "log_path": "90_공통기준/토론모드/logs/debate_*/roundN_cross_verification.md"
  }
}

사용 (β안-C 병렬 호출 직후):
  from bridge.log_bridge import write_cross_verification
  json_path, md_path = write_cross_verification(
      round_n=1,
      gemini_verifies_gpt={"verdict":"동의","reason":"…","model_id":"gemini-2.5-flash"},
      gpt_verifies_gemini={"verdict":"이의","reason":"…","model_id":"gpt-4o"},
      log_dir="90_공통기준/토론모드/logs/debate_20260420_190020_beta_3way",
  )
"""
import json
import pathlib
from typing import Optional

VERDICT_ENUM = {"동의", "이의", "검증 필요"}
REQUIRED_FIELDS = {"verdict", "reason", "model_id"}


def _validate_verification(obj: dict, label: str) -> None:
    if not isinstance(obj, dict):
        raise ValueError(f"{label}: dict 아님 ({type(obj).__name__})")
    missing = REQUIRED_FIELDS - set(obj.keys())
    if missing:
        raise ValueError(f"{label}: 필수 필드 누락 {sorted(missing)}")
    if obj["verdict"] not in VERDICT_ENUM:
        raise ValueError(
            f"{label}.verdict: enum 위반 — 실제 {obj['verdict']!r}, 허용 {sorted(VERDICT_ENUM)}"
        )
    if not isinstance(obj["reason"], str) or len(obj["reason"].strip()) < 4:
        raise ValueError(f"{label}.reason: 근거 1문장 필수 (최소 4자)")
    if not isinstance(obj["model_id"], str) or not obj["model_id"].strip():
        raise ValueError(f"{label}.model_id: 모델 버전 로그 고정 필수")


def build_cross_verification(
    gemini_verifies_gpt: dict,
    gpt_verifies_gemini: dict,
    log_path: str,
) -> dict:
    """β안-C JSON 구조 생성 + 필드 검증."""
    _validate_verification(gemini_verifies_gpt, "gemini_verifies_gpt")
    _validate_verification(gpt_verifies_gemini, "gpt_verifies_gemini")
    if not isinstance(log_path, str) or not log_path.strip():
        raise ValueError("log_path: 비어있음. logs/debate_*/roundN_cross_verification.md 경로 필수")
    return {
        "cross_verification": {
            "gemini_verifies_gpt": gemini_verifies_gpt,
            "gpt_verifies_gemini": gpt_verifies_gemini,
            "log_path": log_path,
        }
    }


def render_markdown(cv: dict, round_n: int) -> str:
    """JSON 스키마를 Claude 6-5 주입용 Markdown으로 렌더링."""
    inner = cv.get("cross_verification", cv)
    ggpt = inner["gemini_verifies_gpt"]
    ggem = inner["gpt_verifies_gemini"]
    lines = [
        f"# Round {round_n} — Cross Verification (β안-C 단발 교차 검증)",
        "",
        "## Gemini → GPT 검증",
        f"- verdict: {ggpt['verdict']}",
        f"- reason: {ggpt['reason']}",
        f"- model_id: `{ggpt['model_id']}`",
        "",
        "## GPT → Gemini 검증",
        f"- verdict: {ggem['verdict']}",
        f"- reason: {ggem['reason']}",
        f"- model_id: `{ggem['model_id']}`",
        "",
        f"> log_path: `{inner['log_path']}`",
    ]
    return "\n".join(lines) + "\n"


def write_cross_verification(
    round_n: int,
    gemini_verifies_gpt: dict,
    gpt_verifies_gemini: dict,
    log_dir: str,
) -> tuple:
    """md + json 이중 기록. SKILL.md β안-C 필수 요구사항.

    반환: (json_path: pathlib.Path, md_path: pathlib.Path)
    """
    log_dir_path = pathlib.Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    md_rel = f"{log_dir}/round{round_n}_cross_verification.md"
    cv = build_cross_verification(gemini_verifies_gpt, gpt_verifies_gemini, md_rel)

    json_path = log_dir_path / f"round{round_n}_cross_verification.json"
    md_path = log_dir_path / f"round{round_n}_cross_verification.md"

    json_path.write_text(
        json.dumps(cv, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_markdown(cv, round_n), encoding="utf-8")
    return json_path, md_path


def inject_prompt_for_round65(cv: dict) -> str:
    """Claude 6-5 종합 프롬프트 상단에 주입할 JSON 원문 문자열 생성."""
    return (
        "## β안-C 단발 교차 검증 결과 (JSON 원문, SKILL.md 필수 주입)\n"
        "```json\n"
        + json.dumps(cv, ensure_ascii=False, indent=2)
        + "\n```\n"
    )


def _self_test() -> int:
    """CLI --self-test. smoke_test 섹션 50에서 호출."""
    ok = True
    try:
        build_cross_verification(
            {"verdict": "동의", "reason": "근거 한 문장.", "model_id": "gemini-2.5-flash"},
            {"verdict": "이의", "reason": "본론 B단계 근거 부족.", "model_id": "gpt-4o"},
            "90_공통기준/토론모드/logs/debate_test/round1_cross_verification.md",
        )
    except Exception as e:
        print(f"[FAIL] happy path: {e}")
        ok = False
    # enum 위반
    try:
        build_cross_verification(
            {"verdict": "모름", "reason": "…", "model_id": "x"},
            {"verdict": "동의", "reason": "…", "model_id": "y"},
            "x.md",
        )
        print("[FAIL] enum 위반이 통과됨")
        ok = False
    except ValueError:
        pass
    # 필수 필드 누락
    try:
        build_cross_verification(
            {"verdict": "동의"},
            {"verdict": "동의", "reason": "…", "model_id": "y"},
            "x.md",
        )
        print("[FAIL] 필수 필드 누락이 통과됨")
        ok = False
    except ValueError:
        pass
    # log_path 비어있음
    try:
        build_cross_verification(
            {"verdict": "동의", "reason": "근거.", "model_id": "m"},
            {"verdict": "동의", "reason": "근거.", "model_id": "m"},
            "",
        )
        print("[FAIL] 빈 log_path가 통과됨")
        ok = False
    except ValueError:
        pass
    if ok:
        print("[PASS] log_bridge self-test 4/4")
        return 0
    return 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(_self_test())
    print("usage: python log_bridge.py --self-test")
    sys.exit(2)
