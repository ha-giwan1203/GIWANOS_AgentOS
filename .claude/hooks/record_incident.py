#!/usr/bin/env python3
"""incident_ledger.jsonl에 구조화된 인시던트를 기록하는 Python CLI 유틸.

hook_common.sh의 hook_incident()와 동일 포맷으로 JSONL 1행을 추가한다.
bash 외부(스킬 커맨드, Python 스크립트 등)에서 인시던트를 기록할 때 사용.

세션45 B1: GPT 판정 structured incident 적재 / D1: 사용자 교정 피드백 적재

Usage:
  python3 .claude/hooks/record_incident.py \\
    --type gpt_verdict \\
    --hook gpt-read \\
    --detail "GPT 판정: 부분반영" \\
    --field source=gpt \\
    --field verdict=partial \\
    --field classification_reason=gpt_verdict

  python3 .claude/hooks/record_incident.py \\
    --type user_correction \\
    --hook manual \\
    --detail "사용자 교정: 경로 오류 수정" \\
    --field source=user \\
    --field verdict=correction \\
    --field classification_reason=user_correction
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def record_incident(
    ledger_path: Path,
    type_: str,
    hook: str,
    file_: str,
    detail: str,
    extra: dict[str, str],
) -> dict:
    """인시던트 1건을 JSONL로 기록. 기록된 엔트리를 반환."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "ts": ts,
        "type": type_,
        "hook": hook,
        "file": file_,
        "detail": detail,
        "resolved": False,
    }
    entry.update(extra)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def parse_field(field_str: str) -> tuple[str, str]:
    """'key=value' 형태의 필드 파싱."""
    if "=" not in field_str:
        raise argparse.ArgumentTypeError(f"필드 형식 오류: '{field_str}' — 'key=value' 형태 필요")
    key, _, value = field_str.partition("=")
    return key.strip(), value.strip()


def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="incident_ledger.jsonl에 구조화된 인시던트 기록"
    )
    parser.add_argument("--ledger", type=str, default=".claude/incident_ledger.jsonl",
                        help="incident ledger 경로")
    parser.add_argument("--type", type=str, required=True,
                        help="인시던트 유형 (gate_reject, gpt_verdict, user_correction 등)")
    parser.add_argument("--hook", type=str, required=True,
                        help="트리거 hook 이름 (필수, 세션107 B-2 강화)")
    parser.add_argument("--file", type=str, default="",
                        help="관련 파일 경로 (없으면 빈 문자열)")
    parser.add_argument("--detail", type=str, required=True,
                        help="상세 설명")
    parser.add_argument("--field", action="append", default=[],
                        help="추가 JSON 필드 (key=value, 복수 가능)")
    parser.add_argument("--quiet", action="store_true",
                        help="성공 시 출력 생략")
    args = parser.parse_args()

    extra: dict[str, str] = {}
    for f in args.field:
        k, v = parse_field(f)
        extra[k] = v

    ledger_path = Path(args.ledger)
    entry = record_incident(ledger_path, args.type, args.hook, args.file, args.detail, extra)

    if not args.quiet:
        print(json.dumps(entry, ensure_ascii=False))


if __name__ == "__main__":
    main()
