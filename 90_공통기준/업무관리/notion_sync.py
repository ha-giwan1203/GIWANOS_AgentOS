"""
notion_sync.py — Phase 5 Notion 자동 동기화 엔진
- Phase 3 결과(STATUS/TASKS 갱신)를 Notion 페이지에 자동 반영
- STATUS 페이지: 자동 감지 변경 이력 섹션에 배치 이벤트 append
- TASKS 페이지: 자동 생성 태스크 섹션에 신규 항목 append
- batch_id 기반 중복 방지
"""

import fnmatch
import json
import logging
import os
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import yaml

# ── 상수 ─────────────────────────────────────────────────────────────────

CONFIG_PATH   = Path(__file__).parent / "notion_config.yaml"
DEDUP_STATE   = Path(__file__).parent / ".notion_dedup_state.json"
NOTION_API    = "https://api.notion.com/v1"
NOTION_VER    = "2022-06-28"


# ── 설정 / 토큰 로드 ──────────────────────────────────────────────────────

def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_token(cfg: dict) -> str:
    env_key = cfg["notion"].get("token_env", "NOTION_TOKEN")
    token = os.environ.get(env_key, "")
    if token.startswith("ntn_") or token.startswith("secret_"):
        return token
    fallback = cfg["notion"].get("token_env_fallback_path", "")
    if fallback:
        fp = Path(fallback)
        if fp.exists():
            for line in fp.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith(env_key + "="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val.startswith("ntn_") or val.startswith("secret_"):
                        return val
    return ""


def setup_error_logger(cfg: dict) -> logging.Logger:
    repo_root = Path(__file__).parent.parent.parent
    log_dir   = cfg.get("logging", {}).get("log_dir", "90_공통기준/업무관리")
    prefix    = cfg.get("logging", {}).get("error_prefix", "notion_errors_")
    log_path  = repo_root / log_dir / f"{prefix}{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger("notion_errors")
    if not logger.handlers:
        logger.setLevel(logging.ERROR)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        h = logging.FileHandler(log_path, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(h)
    return logger


# ── 중복 방지 ─────────────────────────────────────────────────────────────

def _load_dedup() -> dict:
    if DEDUP_STATE.exists():
        try:
            return json.loads(DEDUP_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_dedup(state: dict):
    try:
        DEDUP_STATE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _is_dup(batch_id: str, hours: int) -> bool:
    state = _load_dedup()
    if batch_id not in state:
        return False
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    return state[batch_id] > cutoff


def _mark_done(batch_id: str, hours: int):
    state = _load_dedup()
    state[batch_id] = datetime.now().isoformat()
    cutoff = (datetime.now() - timedelta(hours=hours * 2)).isoformat()
    state = {k: v for k, v in state.items() if v > cutoff}
    _save_dedup(state)


# ── Notion API 헬퍼 ───────────────────────────────────────────────────────

def _notion_request(method: str, endpoint: str, token: str,
                    payload: dict = None, retry: int = 2,
                    delay: int = 3, logger: logging.Logger = None) -> dict | None:
    url  = f"{NOTION_API}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {
        "Authorization":  f"Bearer {token}",
        "Notion-Version": NOTION_VER,
        "Content-Type":   "application/json",
    }
    for attempt in range(retry + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404 and logger:
                logger.error(
                    f"Notion 404 {endpoint} — 페이지에 'GPT 자동 분류 시스템' 통합 앱 연결 필요. "
                    "Notion 페이지 우상단 '...' → '연결' → 'GPT 자동 분류 시스템' 선택"
                )
                return None
            if attempt < retry:
                time.sleep(delay)
            elif logger:
                logger.error(f"Notion API 오류 {endpoint}: {e}")
        except Exception as e:
            if attempt < retry:
                time.sleep(delay)
            elif logger:
                logger.error(f"Notion API 오류 {endpoint}: {e}")
    return None


def _append_blocks(page_id: str, blocks: list, token: str,
                   logger: logging.Logger) -> bool:
    """페이지에 블록 추가."""
    pid = page_id.replace("-", "")
    result = _notion_request(
        "PATCH", f"/blocks/{pid}/children",
        token, {"children": blocks}, logger=logger
    )
    return result is not None


def _delete_block(block_id: str, token: str, logger: logging.Logger) -> bool:
    """블록 삭제 (archived=true)."""
    result = _notion_request("DELETE", f"/blocks/{block_id}", token, logger=logger)
    return result is not None


# ── 이력 보존 정책 ──────────────────────────────────────────────────────

MAX_HISTORY_ENTRIES = 20  # 이력 항목(divider 기준) 최대 보존 수


def _trim_history_blocks(page_id: str, token: str, logger: logging.Logger,
                         max_entries: int = MAX_HISTORY_ENTRIES) -> int:
    """페이지 하단 이력 블록을 최근 N개만 유지. 초과분 삭제. 삭제 건수 반환."""
    blocks = _get_page_blocks(page_id, token)
    if not blocks:
        return 0

    # '자동 감지 변경 이력' 또는 '자동 생성 태스크' 헤딩 이후 블록 수집
    history_start = -1
    for i, b in enumerate(blocks):
        btype = b.get("type", "")
        if btype in ("heading_2", "heading_3"):
            rich = b.get(btype, {}).get("rich_text", [])
            text = "".join(r.get("plain_text", "") for r in rich)
            if "이력" in text or "태스크" in text:
                history_start = i + 1
                break

    if history_start < 0:
        return 0

    # divider 블록을 entry 구분자로 사용 — divider 수 = entry 수
    history_blocks = blocks[history_start:]
    entries = []  # [(start_idx, [block_ids])]
    current_entry_blocks = []

    for b in history_blocks:
        if b.get("type") == "divider":
            if current_entry_blocks:
                entries.append(current_entry_blocks)
            current_entry_blocks = [b["id"]]
        else:
            current_entry_blocks.append(b["id"])

    if current_entry_blocks:
        entries.append(current_entry_blocks)

    if len(entries) <= max_entries:
        return 0

    # 오래된 것부터 삭제 (entries[0]이 가장 오래됨)
    to_delete = entries[:len(entries) - max_entries]
    deleted = 0
    for entry_block_ids in to_delete:
        for bid in entry_block_ids:
            if _delete_block(bid, token, logger):
                deleted += 1

    if logger and deleted > 0:
        logger.error(
            f"이력 보존 정책: {len(entries)}개 중 {len(to_delete)}개 항목({deleted}블록) 삭제 → {max_entries}개 유지"
        )
    return deleted


def _get_page_blocks(page_id: str, token: str) -> list:
    """페이지 최상위 블록 목록 조회 (pagination 지원)."""
    pid = page_id.replace("-", "")
    all_blocks = []
    cursor = None
    while True:
        endpoint = f"/blocks/{pid}/children?page_size=100"
        if cursor:
            endpoint += f"&start_cursor={cursor}"
        result = _notion_request("GET", endpoint, token, logger=None)
        if not result:
            break
        all_blocks.extend(result.get("results", []))
        if result.get("has_more"):
            cursor = result.get("next_cursor")
        else:
            break
    return all_blocks


def _find_heading_block_id(blocks: list, heading_text: str) -> str | None:
    """특정 제목 블록의 ID 반환."""
    for b in blocks:
        btype = b.get("type", "")
        if btype in ("heading_2", "heading_3"):
            rich = b.get(btype, {}).get("rich_text", [])
            text = "".join(r.get("plain_text", "") for r in rich)
            if heading_text in text:
                return b["id"]
    return None


# ── 블록 조립 ─────────────────────────────────────────────────────────────

def _text_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
    }


def _bullet_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
    }


def _heading3_block(text: str) -> dict:
    # is_toggleable=True 필수 — False면 heading block에 children append 불가 (Notion API 제한)
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "is_toggleable": True,
        }
    }


def _divider_block() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


# ── 요약 블록 갱신 ───────────────────────────────────────────────────────

SUMMARY_MARKER = "요약 (Git/TASKS.md 기준 자동 동기화 대상)"


def _parse_tasks_summary(repo_root: Path) -> dict:
    """TASKS.md를 파싱하여 요약 데이터 반환."""
    tasks_path = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    if not tasks_path.exists():
        return {}

    text = tasks_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_progress = 0
    pending = 0
    completed = 0
    section = ""
    progress_names = []
    pending_names = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## 진행 중"):
            section = "progress"
        elif stripped.startswith("## 대기 중"):
            section = "pending"
        elif stripped.startswith("## 완료됨"):
            section = "done"
        elif stripped.startswith("## "):
            section = ""

        if section == "progress" and stripped.startswith("### ") and "~~" not in stripped:
            in_progress += 1
            name = stripped.lstrip("# ").strip()
            progress_names.append(name)
        elif section == "pending" and stripped.startswith("### ") and "~~" not in stripped:
            pending += 1
            name = stripped.lstrip("# ").strip()
            # 차단 사유 추출 — "**차단:" 패턴
            block_reason = ""
            if "차단:" in name or "차단：" in name:
                block_reason = name.split("차단")[-1].strip(":： —*").strip()
            pending_names.append((name, block_reason))
        elif section == "done" and stripped.startswith("|") and "항목" not in stripped and "---" not in stripped:
            completed += 1

    return {
        "in_progress": in_progress,
        "pending": pending,
        "completed": completed,
        "progress_names": progress_names,
        "pending_names": pending_names,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
    }


def _find_summary_content_blocks(blocks: list) -> list:
    """요약 heading 아래 연속 bullet/paragraph 블록 ID 목록 반환."""
    found_heading = False
    result_ids = []
    for b in blocks:
        btype = b.get("type", "")
        if btype in ("heading_2", "heading_3"):
            rich = b.get(btype, {}).get("rich_text", [])
            text = "".join(r.get("plain_text", "") for r in rich)
            if "요약" in text:
                found_heading = True
                continue
            elif found_heading:
                break  # 다음 heading → 종료
        elif found_heading:
            if btype in ("bulleted_list_item", "paragraph", "divider"):
                result_ids.append((b["id"], btype))
            else:
                break  # 다른 블록 타입 → 종료
    return result_ids


def _build_summary_lines(summary: dict) -> list:
    """요약 데이터로 bullet 텍스트 목록 생성."""
    # 진행 중 상세
    prog_count = summary.get("in_progress", 0)
    prog_names = summary.get("progress_names", [])
    if prog_count > 0 and prog_names:
        progress_text = f"진행 중: {prog_count}건 ({', '.join(prog_names[:3])})"
    else:
        progress_text = f"진행 중: {prog_count}건"

    # 대기 중 상세
    pend_count = summary.get("pending", 0)
    pend_names = summary.get("pending_names", [])
    if pend_count > 0 and pend_names:
        details = []
        for name, reason in pend_names[:3]:
            # 짧은 이름 추출 (### 제거, [auto] 등 태그 정리)
            short = name.replace("[auto]", "").strip().split("—")[0].strip()
            if reason:
                details.append(f"{short} — {reason}")
            else:
                details.append(short)
        pending_text = f"대기 중: {pend_count}건 ({', '.join(details)})"
    else:
        pending_text = f"대기 중: {pend_count}건"

    return [
        progress_text,
        pending_text,
        f"완료: {summary.get('completed', 0)}건",
        "자동화 체인: 정상 (watch_changes + auto-commit + Slack + Notion)",
        f"동기화: {summary.get('timestamp', '')}",
    ]


def _update_summary_blocks(content_blocks: list, summary: dict, token: str,
                           logger: logging.Logger) -> tuple:
    """요약 아래 bullet 블록들을 순서대로 업데이트. (before, after) 스냅샷 반환."""
    lines = _build_summary_lines(summary)

    before_snapshot = []
    after_snapshot = []
    ok = True
    updated_count = 0

    for i, (block_id, btype) in enumerate(content_blocks):
        if i >= len(lines):
            break
        if btype != "bulleted_list_item":
            continue

        # before 스냅샷: 현재 블록 내용 읽기
        current = _notion_request("GET", f"/blocks/{block_id}", token, logger=logger)
        if current:
            rich = current.get("bulleted_list_item", {}).get("rich_text", [])
            old_text = "".join(r.get("plain_text", "") for r in rich)
            before_snapshot.append(old_text)
        else:
            before_snapshot.append("(읽기 실패)")

        # 업데이트
        result = _notion_request(
            "PATCH", f"/blocks/{block_id}", token,
            {"bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": lines[i]}}]
            }},
            logger=logger,
        )
        if result is None:
            ok = False
            after_snapshot.append("(갱신 실패)")
            if logger:
                logger.error(f"요약 블록 갱신 실패: block_id={block_id}, line={lines[i]}")
        else:
            after_snapshot.append(lines[i])
            updated_count += 1

    # 부분 갱신 감지 — 즉시 중단 조건
    if 0 < updated_count < len(lines) and updated_count < len(content_blocks):
        if logger:
            logger.error(
                f"요약 블록 부분 갱신 감지: {updated_count}/{min(len(lines), len(content_blocks))}건만 성공"
            )
        ok = False

    return ok, before_snapshot, after_snapshot


def update_summary(token: str, cfg: dict, repo_root: Path,
                   logger: logging.Logger) -> bool:
    """STATUS 페이지의 요약 블록을 TASKS.md 기준으로 갱신.

    즉시 중단 조건 3가지:
    1. 페이지 못 찾음 (blocks 빈 목록)
    2. 요약 블록 매칭 실패 (content_blocks 없음)
    3. 부분 갱신 (_update_summary_blocks에서 감지)
    """
    page_id = cfg["notion"]["status_page_id"]
    summary = _parse_tasks_summary(repo_root)
    if not summary:
        if logger:
            logger.error("TASKS.md 파싱 실패 — 파일 없거나 빈 결과")
        return False

    blocks = _get_page_blocks(page_id, token)
    if not blocks:
        if logger:
            logger.error(f"Notion 페이지 블록 조회 실패: page_id={page_id}")
        return False

    content_blocks = _find_summary_content_blocks(blocks)
    if not content_blocks:
        if logger:
            logger.error("Notion 요약 콘텐츠 블록을 찾지 못함 — '요약' 헤딩 아래 bullet 없음")
        return False

    ok, before, after = _update_summary_blocks(content_blocks, summary, token, logger)

    # 검증 로그: before/after 스냅샷 비교
    if logger and before and after:
        verify_logger = logging.getLogger("notion_sync_verify")
        if not verify_logger.handlers:
            verify_logger.setLevel(logging.INFO)
            log_dir = Path(__file__).parent
            vlog = log_dir / f"notion_sync_verify_{datetime.now().strftime('%Y%m%d')}.log"
            h = logging.FileHandler(vlog, encoding="utf-8")
            h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            verify_logger.addHandler(h)
        verify_logger.info(f"=== 요약 갱신 검증 ===")
        for i, (b, a) in enumerate(zip(before, after)):
            changed = "변경" if b != a else "동일"
            verify_logger.info(f"  [{i}] {changed}: '{b}' → '{a}'")
        verify_logger.info(f"  결과: {'PASS' if ok else 'FAIL'}")

    return ok


# ── STATUS 페이지 동기화 ──────────────────────────────────────────────────

def _has_critical(events: list, patterns: list) -> list:
    hits = []
    for abs_path, _ in events:
        fname = Path(abs_path).name
        if any(fnmatch.fnmatch(fname, p) for p in patterns):
            hits.append(fname)
    return hits


def sync_status_page(batch_id: str, events: list, phase3_result: dict,
                     phase2_result: dict, token: str, cfg: dict,
                     logger: logging.Logger) -> bool:
    """
    STATUS 페이지의 '자동 감지 변경 이력' 섹션에 배치 이벤트 append.
    섹션이 없으면 생성.
    """
    page_id  = cfg["notion"]["status_page_id"]
    patterns = cfg["notion"].get("critical_patterns", [])
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 추가할 내용 조립
    lines = []
    critical = _has_critical(events, patterns)
    if critical:
        lines.append(f"핵심 파일 변경: {', '.join(critical)}")
    if phase3_result.get("ok") and phase3_result.get("modified"):
        updated = ", ".join(Path(p).name for p in phase3_result["modified"])
        lines.append(f"STATUS/TASKS 갱신: {updated}")
    committed = (phase2_result or {}).get("committed", 0)
    sha = (phase2_result or {}).get("commit_sha", "")
    if committed > 0:
        lines.append(f"Git 커밋 {committed}건 ({sha[:7] if sha else '-'})")
    if not lines:
        return True  # 기록할 내용 없음

    summary = f"[{ts}] 배치 {batch_id[:8]} | 파일 {len(events)}건"

    # 항상 페이지 하단에 직접 append (heading-as-container 방식 폐기)
    # heading block은 is_toggleable=True 없으면 children append 불가 (Notion API 400)
    new_blocks = [
        _divider_block(),
        _text_block(summary),
    ] + [_bullet_block(l) for l in lines]
    return _append_blocks(page_id, new_blocks, token, logger)


# ── TASKS 페이지 동기화 ───────────────────────────────────────────────────

def sync_tasks_page(batch_id: str, events: list, phase3_result: dict,
                    token: str, cfg: dict, logger: logging.Logger) -> bool:
    """
    TASKS 페이지의 '자동 생성 태스크' 섹션에 신규 항목 append.
    Phase 3가 TASKS.md에 [auto] 항목을 추가했을 때만 동작.
    """
    # TASKS.md가 phase3 수정 목록에 없으면 동작 안 함
    modified = phase3_result.get("modified", [])
    if not any("TASKS" in str(p) for p in modified):
        return True

    page_id = cfg["notion"]["tasks_page_id"]
    ts      = datetime.now().strftime("%Y-%m-%d %H:%M")

    # TASKS.md에서 최근 추가된 [auto] 항목 읽기
    repo_root = Path(__file__).parent.parent.parent
    tasks_path = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    auto_items = []
    if tasks_path.exists():
        for line in tasks_path.read_text(encoding="utf-8").splitlines():
            if "[auto]" in line:
                auto_items.append(line.strip().lstrip("- ").replace("[auto]", "").strip())

    if not auto_items:
        return True

    # 항상 페이지 하단에 직접 append (heading-as-container 방식 폐기)
    summary    = f"[{ts}] 배치 {batch_id[:8]} — {len(auto_items)}건 자동 추가"
    new_blocks = [
        _divider_block(),
        _text_block(summary),
    ] + [_bullet_block(i) for i in auto_items[:10]]
    return _append_blocks(page_id, new_blocks, token, logger)


# ── 핵심: 배치 동기화 ─────────────────────────────────────────────────────

def sync_batch(batch_id: str, events: list,
               phase3_result: dict = None,
               phase2_result: dict = None,
               cfg: dict = None,
               dry_run: bool = False,
               logger: logging.Logger = None) -> bool:
    if cfg is None:
        cfg = load_config()
    if logger is None:
        logger = setup_error_logger(cfg)

    notion_cfg  = cfg.get("notion", {})
    dedup_hours = notion_cfg.get("dedup_window_hours", 1)
    sync_on     = notion_cfg.get("sync_on", {})
    patterns    = notion_cfg.get("critical_patterns", [])

    # 동기화 조건 확인
    should_sync = False
    if sync_on.get("status_tasks_updated") and (phase3_result or {}).get("ok"):
        should_sync = True
    if sync_on.get("critical_file_changed") and _has_critical(events, patterns):
        should_sync = True
    if not should_sync:
        return True

    # 중복 방지 — STATUS/TASKS 페이지별 독립 추적 (부분 성공 재실행 시 중복 append 방지)
    status_done = _is_dup(batch_id + "_s", dedup_hours)
    tasks_done  = _is_dup(batch_id + "_t", dedup_hours)
    if status_done and tasks_done:
        return True

    if dry_run:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"[DRY-RUN NOTION] [{ts}] 배치 {batch_id[:8]} | 파일 {len(events)}건")
        return True

    token = load_token(cfg)
    if not token:
        logger.error("Notion 토큰 없음 — NOTION_TOKEN 환경변수 또는 .env 파일 확인")
        return False

    ok1 = False if not status_done else True
    ok2 = False if not tasks_done else True

    if not status_done:
        ok1 = sync_status_page(batch_id, events, phase3_result or {}, phase2_result or {},
                               token, cfg, logger)
        if ok1:
            _mark_done(batch_id + "_s", dedup_hours)

    if not tasks_done:
        ok2 = sync_tasks_page(batch_id, events, phase3_result or {},
                              token, cfg, logger)
        if ok2:
            _mark_done(batch_id + "_t", dedup_hours)

    # 요약 블록 갱신 — 실패 시 배치 결과에 반영 (조용한 실패 방지)
    ok3 = True
    try:
        repo_root = Path(__file__).parent.parent.parent
        ok3 = update_summary(token, cfg, repo_root, logger)
    except Exception as e:
        ok3 = False
        if logger:
            logger.error(f"요약 블록 갱신 예외: {e}")

    # 이력 보존 정책 — 오래된 이력 자동 삭제
    max_entries = notion_cfg.get("max_history_entries", MAX_HISTORY_ENTRIES)
    try:
        status_pid = notion_cfg["status_page_id"]
        _trim_history_blocks(status_pid, token, logger, max_entries)
    except Exception as e:
        if logger:
            logger.error(f"이력 정리 실패 (무시): {e}")

    return ok1 and ok2 and ok3


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 5 Notion 동기화 테스트")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-id", default="test1234")
    args = parser.parse_args()

    cfg    = load_config()
    logger = setup_error_logger(cfg)

    test_events   = [
        ("C:/Users/User/Desktop/업무리스트/CLAUDE.md", {"event_type": "modified"}),
    ]
    test_phase3 = {"ok": True, "modified": ["STATUS.md", "TASKS.md"]}
    test_phase2 = {"committed": 1, "commit_sha": "abc1234def"}

    ok = sync_batch(
        batch_id=args.batch_id,
        events=test_events,
        phase3_result=test_phase3,
        phase2_result=test_phase2,
        cfg=cfg,
        dry_run=args.dry_run,
        logger=logger,
    )
    print("Notion 동기화 성공" if ok else "Notion 동기화 실패")


if __name__ == "__main__":
    main()
