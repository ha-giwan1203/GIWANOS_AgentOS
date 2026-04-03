#!/usr/bin/env bash
# Stop hook — dirty.flag + verify.json PASS 필수 완료 게이트
# 파일 변경이 있었는데 검증을 안 했으면 완료 보고를 차단한다.
# GPT 합의 2026-04-01: 1단계 구조적 가드레일
set -euo pipefail
source "$(dirname "$0")/hook_common.sh" 2>/dev/null || true
hook_log "Stop" "pre_finish_guard 발화" 2>/dev/null || true

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TMP_INPUT="$(mktemp)"
cat > "$TMP_INPUT"

python3 - "$ROOT" "$TMP_INPUT" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
input_path = pathlib.Path(sys.argv[2])

payload = json.loads(input_path.read_text(encoding="utf-8"))
last_msg = payload.get("last_assistant_message", "") or ""
stop_hook_active = bool(payload.get("stop_hook_active", False))

state_dir = root / "90_공통기준" / "agent-control" / "state"
current_task_file = state_dir / "current_task"
dirty_flag = state_dir / "dirty.flag"

def block(reason: str) -> None:
    print(json.dumps({
        "decision": "block",
        "reason": reason
    }, ensure_ascii=False))
    raise SystemExit(0)

def read_current_task_dir():
    if not current_task_file.exists():
        return None
    raw = current_task_file.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    task_dir = (root / raw).resolve() if not pathlib.Path(raw).is_absolute() else pathlib.Path(raw).resolve()
    return task_dir

def parse_plan(plan_path: pathlib.Path) -> dict:
    text = plan_path.read_text(encoding="utf-8")
    verify_required = bool(re.search(r'^\s*verify_required\s*:\s*true\s*$', text, re.I | re.M))
    return {"verify_required": verify_required}

def looks_like_completion(text: str) -> bool:
    """완료 보고처럼 보이는 패턴 감지"""
    patterns = [
        r'완료',
        r'PASS',
        r'성공',
        r'반영.*했',
        r'커밋',
        r'갱신.*완료',
    ]
    return any(re.search(p, text) for p in patterns)

# === 메인 로직 ===

# current_task가 없으면 게이트 비활성
task_dir = read_current_task_dir()
if task_dir is None:
    raise SystemExit(0)

# dirty.flag가 없으면 파일 변경 없음 → 통과
if not dirty_flag.exists():
    raise SystemExit(0)

# 완료 보고 패턴이 아니면 통과 (중간 응답은 차단하지 않음)
if not looks_like_completion(last_msg):
    raise SystemExit(0)

# plan.md 확인
plan_path = task_dir / "plan.md"
if not plan_path.exists():
    block("plan.md 가 없습니다. plan.md와 verify.json PASS 없이 완료 보고할 수 없습니다.")

plan = parse_plan(plan_path)
if not plan["verify_required"]:
    # 검증 불필요 작업이면 통과
    raise SystemExit(0)

# verify.json 확인
verify_path = task_dir / "verify.json"
if not verify_path.exists():
    block("verify.json 이 없습니다. verifier를 실행하고 PASS 결과를 만든 뒤 완료 보고하세요.")

try:
    verify = json.loads(verify_path.read_text(encoding="utf-8"))
except Exception:
    block("verify.json 파싱 실패. verifier를 다시 실행하세요.")

status = str(verify.get("status", "")).lower().strip()
if status != "pass":
    block("verify.json status=pass 가 아닙니다. 실패 원인 수정 후 다시 검증하세요.")

# verify.json이 dirty.flag보다 오래됐으면 재검증 필요
if dirty_flag.exists() and verify_path.exists():
    if verify_path.stat().st_mtime < dirty_flag.stat().st_mtime:
        block("verify.json 이 최신 변경보다 오래되었습니다. 변경 후 verifier를 다시 실행하세요.")

# 모든 게이트 통과 → dirty.flag 제거
dirty_flag.unlink(missing_ok=True)
raise SystemExit(0)
PY

rm -f "$TMP_INPUT"
