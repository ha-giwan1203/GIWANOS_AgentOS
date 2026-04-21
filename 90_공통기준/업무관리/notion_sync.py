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
import sys
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


# ── 부모 페이지 동기화 ────────────────────────────────────────────────────

PARENT_SECTION_HEADING = "📌 운영 현황"


def _parse_parent_summary(repo_root: Path) -> list[str]:
    """HANDOFF(세션 번호) + TASKS(최근 완료 3건)에서 부모 페이지 요약 생성."""
    lines = []

    # HANDOFF에서 최신 세션 번호 추출
    handoff = repo_root / "90_공통기준" / "업무관리" / "HANDOFF.md"
    if handoff.exists():
        for line in handoff.read_text(encoding="utf-8").splitlines():
            if line.startswith("최종 업데이트:"):
                lines.append(line.strip())
                break

    # TASKS에서 최근 완료 항목 3건 추출
    tasks = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    if tasks.exists():
        in_completed = False
        count = 0
        for line in tasks.read_text(encoding="utf-8").splitlines():
            if "## 최근 완료" in line:
                in_completed = True
                continue
            if in_completed and line.startswith("### [완료]"):
                item = line.replace("### ", "").strip()
                lines.append(item)
                count += 1
                if count >= 3:
                    break
            if in_completed and line.startswith("## ") and "완료" not in line:
                break

    return lines


def sync_parent_page(token: str, cfg: dict, repo_root: Path,
                     logger: logging.Logger) -> bool:
    """부모 페이지 '운영 현황' 섹션만 블록 단위 갱신 (best-effort)."""
    parent_id = cfg["notion"].get("parent_page_id", "")
    if not parent_id:
        return True  # optional — 설정 없으면 skip

    summary_lines = _parse_parent_summary(repo_root)
    if not summary_lines:
        if logger:
            logger.info("부모 페이지 요약 데이터 없음 — skip")
        return True

    blocks = _get_page_blocks(parent_id, token)
    if not blocks:
        if logger:
            logger.error(f"부모 페이지 블록 조회 실패: page_id={parent_id}")
        return False

    # "운영 현황" 헤딩 다음 블록들을 찾아서 교체
    heading_idx = None
    for i, b in enumerate(blocks):
        btype = b.get("type", "")
        if btype == "heading_2":
            rich = b.get("heading_2", {}).get("rich_text", [])
            text = "".join(r.get("plain_text", "") for r in rich)
            if PARENT_SECTION_HEADING in text:
                heading_idx = i
                break

    if heading_idx is None:
        if logger:
            logger.error(f"부모 페이지에서 '{PARENT_SECTION_HEADING}' 헤딩 없음")
        return False

    # 헤딩 다음부터 다음 heading_2 또는 divider까지의 블록 삭제
    to_delete = []
    for j in range(heading_idx + 1, len(blocks)):
        bt = blocks[j].get("type", "")
        if bt in ("heading_2", "divider"):
            break
        to_delete.append(blocks[j]["id"])

    for bid in to_delete:
        _delete_block(bid, token, logger)

    # 새 블록 삽입 — 헤딩 바로 아래 append (after 파라미터 사용)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_blocks = [
        _text_block(f"자동 갱신: {ts}"),
        _text_block("운영 요약·작업 현황·완료 이력은 아래 페이지에서 확인:"),
    ]
    for line in summary_lines:
        new_blocks.append(_bullet_block(line))

    # heading 블록의 after에 삽입
    heading_block_id = blocks[heading_idx]["id"]
    pid = parent_id.replace("-", "")
    result = _notion_request(
        "PATCH", f"/blocks/{pid}/children",
        token, {
            "children": new_blocks,
            "position": {"type": "after_block", "after_block": {"id": heading_block_id}},
        }, logger=logger
    )
    return result is not None


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

    # 부모 페이지 동기화 (best-effort — 실패해도 배치 결과 불승격)
    parent_done = _is_dup(batch_id + "_p", dedup_hours)
    if not parent_done and notion_cfg.get("parent_page_id"):
        try:
            repo_root = Path(__file__).parent.parent.parent
            ok_parent = sync_parent_page(token, cfg, repo_root, logger)
            if ok_parent:
                _mark_done(batch_id + "_p", dedup_hours)
            elif logger:
                logger.warning("부모 페이지 동기화 실패 (배치 결과에 영향 없음)")
        except Exception as e:
            if logger:
                logger.warning(f"부모 페이지 동기화 예외 (무시): {e}")

    # 이력 보존 정책 — 오래된 이력 자동 삭제
    max_entries = notion_cfg.get("max_history_entries", MAX_HISTORY_ENTRIES)
    try:
        status_pid = notion_cfg["status_page_id"]
        _trim_history_blocks(status_pid, token, logger, max_entries)
    except Exception as e:
        if logger:
            logger.error(f"이력 정리 실패 (무시): {e}")

    return ok1 and ok2 and ok3


import re as _re  # 세션86 오후 별건: 최종 업데이트 라인 파싱용
import subprocess as _sp  # 세션88 3way: snapshot 필드 수집용


# ── SYNC_START/END marker zone (세션88 3way 합의) ─────────────────────────
# 합의안: Notion 본문 정체(세션45 시점 고정) 해소. generated snapshot 블록을
# STATUS 상단 marker 내부에만 덮어쓰기(append 금지). 허위 이력 append 방지(세션86) 원칙 유지.
# 로그: 90_공통기준/토론모드/logs/debate_20260421_160431_3way/

SYNC_MARKER_START = "<!-- SYNC_START (auto-generated, do not edit manually) -->"
SYNC_MARKER_END   = "<!-- SYNC_END -->"
SYNC_EDIT_WARNING = "⚠️ 이 블록은 notion_sync.py가 자동 생성합니다. 수동 편집 금지 (덮어쓰기로 소실됨)"
SNAPSHOT_PATH     = Path(__file__).parent / "notion_snapshot.json"


def _run_cmd(args: list[str], cwd: Path, timeout: int = 5) -> str:
    """외부 명령 실행 결과 반환. 실패 시 빈 문자열."""
    try:
        r = _sp.run(args, cwd=str(cwd), capture_output=True, text=True,
                    timeout=timeout, encoding="utf-8", errors="ignore")
        return (r.stdout or "").strip()
    except Exception:
        return ""


def _count_hooks(repo_root: Path) -> tuple[int, int]:
    """훅 수 반환: (raw 파일 수, settings.json 등록 수).

    raw: .claude/hooks/*.sh 파일 개수
    활성: settings.json(team) + settings.local.json(personal) hooks 블록에서 실제 등록된
          .claude/hooks/*.sh 경로 수 (중복 제거). GPT 세션88 A분류 지적 반영.
    """
    hooks_dir = repo_root / ".claude" / "hooks"
    raw = 0
    if hooks_dir.exists():
        raw = sum(1 for p in hooks_dir.glob("*.sh") if p.is_file())

    active_commands: set[str] = set()
    for name in ("settings.json", "settings.local.json"):
        sf = repo_root / ".claude" / name
        if not sf.exists():
            continue
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        hooks = data.get("hooks", {})
        if not isinstance(hooks, dict):
            continue
        for _event, matchers in hooks.items():
            if not isinstance(matchers, list):
                continue
            for m in matchers:
                if not isinstance(m, dict):
                    continue
                for h in m.get("hooks", []):
                    if isinstance(h, dict):
                        cmd = h.get("command", "")
                        if isinstance(cmd, str) and cmd:
                            for match in _re.finditer(r'(\.claude/hooks/[^\s"\'`]+\.sh)', cmd):
                                active_commands.add(match.group(1))
    active = len(active_commands) if active_commands else raw
    return raw, active


def _count_commands(repo_root: Path) -> int:
    cmds_dir = repo_root / ".claude" / "commands"
    if not cmds_dir.exists():
        return 0
    return sum(1 for p in cmds_dir.glob("*.md") if p.is_file())


def _read_smoke_result(repo_root: Path) -> str:
    """smoke_test 최근 결과. 저장 파일 없으면 'unknown'.

    smoke_test.sh는 긴 실행이라 실시간 재실행 금지. 저장된 로그 1줄 조회.
    """
    # smoke_test.sh 자체 로그 파일이 없으면 고정값으로 fallback
    log_candidates = [
        repo_root / ".claude" / "state" / "smoke_last_result.txt",
    ]
    for p in log_candidates:
        if p.exists():
            try:
                return p.read_text(encoding="utf-8").strip().splitlines()[0][:30]
            except Exception:
                pass
    return "unknown"


def _parse_recent_sessions(repo_root: Path, n: int = 5) -> list[str]:
    """TASKS.md에서 최근 N개 세션 헤더 추출 ('## 세션NN ...' 라인)."""
    tasks = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    if not tasks.exists():
        return []
    found = []
    try:
        for line in tasks.read_text(encoding="utf-8").splitlines():
            m = _re.match(r"^##\s+(세션\d+.*)", line)
            if m:
                found.append(m.group(1).strip())
                if len(found) >= n:
                    break
    except Exception:
        pass
    return found


def _parse_all_sessions(repo_root: Path, limit: int = 50) -> list[str]:
    """TASKS.md 전체 세션 헤더 목록 추출 (최대 limit개).

    반환 형식: "세션NN — 제목" (제목은 `## 세션NN ...` 헤더에서 파싱)
    """
    tasks = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    if not tasks.exists():
        return []
    found = []
    try:
        for line in tasks.read_text(encoding="utf-8").splitlines():
            m = _re.match(r"^##\s+(세션\d+.*)", line)
            if m:
                found.append(m.group(1).strip()[:200])
                if len(found) >= limit:
                    break
    except Exception:
        pass
    return found


def _parse_sessions_detail(repo_root: Path, limit: int = 20,
                           body_lines_per_session: int = 25) -> list[dict]:
    """TASKS.md 각 세션 블록 파싱 — header + body (bullet/완료 항목).

    반환: [{"header": str, "body": [str, ...]}]
    body에는 "**[완료]**", "**[이월]**", "- ", "  - " 등 주요 라인만 수집.
    세션 구분자: 다음 `## 세션` 또는 EOF.
    """
    tasks = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    if not tasks.exists():
        return []
    result = []
    try:
        lines = tasks.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    i = 0
    while i < len(lines) and len(result) < limit:
        line = lines[i]
        m = _re.match(r"^##\s+(세션\d+.*)", line)
        if not m:
            i += 1
            continue
        header = m.group(1).strip()[:200]
        body: list[str] = []
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if _re.match(r"^##\s+", nxt) or _re.match(r"^---\s*$", nxt):
                break
            stripped = nxt.rstrip()
            if not stripped:
                i += 1
                continue
            # 주요 정보 라인만 수집
            if (stripped.startswith("**[") or
                stripped.startswith("- ") or
                stripped.startswith("  - ") or
                stripped.startswith("    - ")):
                body.append(stripped[:220])
                if len(body) >= body_lines_per_session:
                    break
            i += 1
        result.append({"header": header, "body": body})
        while i < len(lines) and not _re.match(r"^##\s+", lines[i]):
            i += 1
    return result


def generate_snapshot(repo_root: Path) -> dict:
    """Notion snapshot 필드 수집 (TASKS/HANDOFF + git + 파일 수).

    반환 키:
      last_updated, github_sha, github_sha_short, hooks_raw, hooks_active,
      commands, smoke, recent_sessions (list), generated_at
    """
    snap = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
        "last_updated": "",
        "github_sha": "",
        "github_sha_short": "",
        "hooks_raw": 0,
        "hooks_active": 0,
        "commands": 0,
        "smoke": "unknown",
        "recent_sessions": [],
    }

    # TASKS.md 최종 업데이트 라인
    tag = _parse_session_tag(repo_root)
    if tag:
        snap["last_updated"] = tag

    # git SHA
    sha_full = _run_cmd(["git", "log", "-1", "--format=%H"], repo_root)
    sha_short = _run_cmd(["git", "log", "-1", "--format=%h"], repo_root)
    snap["github_sha"] = sha_full
    snap["github_sha_short"] = sha_short

    raw, active = _count_hooks(repo_root)
    snap["hooks_raw"] = raw
    snap["hooks_active"] = active
    snap["commands"] = _count_commands(repo_root)
    snap["smoke"] = _read_smoke_result(repo_root)
    snap["recent_sessions"] = _parse_recent_sessions(repo_root, 5)
    snap["all_sessions"] = _parse_all_sessions(repo_root, 50)
    # 세션 상세: 최근 20세션만 body 포함 (Notion 페이지 비대 방지)
    snap["sessions_detail"] = _parse_sessions_detail(repo_root, limit=20, body_lines_per_session=25)

    return snap


def write_snapshot_json(snap: dict, logger: logging.Logger = None) -> bool:
    """snapshot 결과를 notion_snapshot.json에 저장."""
    try:
        SNAPSHOT_PATH.write_text(
            json.dumps(snap, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception as e:
        if logger:
            logger.error(f"notion_snapshot.json 저장 실패: {e}")
        return False


def _recent_commits(repo_root: Path, n: int = 10) -> list[str]:
    """git log 최근 N건 — 'SHA — subject' 형식."""
    out = _run_cmd(["git", "log", f"-{n}", "--pretty=format:%h — %s"], repo_root, timeout=5)
    return [l for l in out.splitlines() if l.strip()]


def _incident_top_kinds(repo_root: Path, days: int = 7, top: int = 8) -> list[tuple[str, int]]:
    """incident_ledger.jsonl에서 최근 N일 이내 classification/reason 상위 kind 카운트."""
    ledger = repo_root / ".claude" / "incident_ledger.jsonl"
    if not ledger.exists():
        return []
    from collections import Counter
    cutoff = datetime.now() - timedelta(days=days)
    counter: Counter = Counter()
    try:
        with open(ledger, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                ts_str = obj.get("ts") or obj.get("timestamp") or ""
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts.tzinfo is not None:
                        ts = ts.replace(tzinfo=None)
                    if ts < cutoff:
                        continue
                except Exception:
                    pass
                resolved = obj.get("resolved", False)
                if resolved is True:
                    continue
                kind = obj.get("classification") or obj.get("reason") or obj.get("kind") or "unknown"
                counter[str(kind)[:60]] += 1
    except Exception:
        return []
    return counter.most_common(top)


def _recent_auto_recovery(repo_root: Path, n: int = 5) -> list[str]:
    """auto_recovery.jsonl 최근 N건 행동 요약."""
    rec = repo_root / ".claude" / "self" / "auto_recovery.jsonl"
    if not rec.exists():
        return []
    out = []
    try:
        with open(rec, encoding="utf-8", errors="ignore") as f:
            for line in f.readlines()[-n:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ts = obj.get("ts") or obj.get("date") or ""
                    action = obj.get("action") or "?"
                    detail_keys = [k for k in obj.keys() if k not in ("ts", "date", "action")]
                    detail = " / ".join(f"{k}={obj[k]}" for k in detail_keys[:3])
                    out.append(f"{ts} · {action}" + (f" · {detail}" if detail else ""))
                except Exception:
                    pass
    except Exception:
        return []
    return out


def _build_status_blocks(snap: dict, repo_root: Path) -> list[dict]:
    """STATUS (Auto) — 시스템 운영 현황. 실질적 상태 정보 중심."""
    blocks = [
        _text_block(SYNC_EDIT_WARNING),
        _text_block(f"자동 갱신: {snap.get('generated_at', '')}"),
        _divider_block(),
    ]

    # ── System Health (Self-X Layer 1 invariants 전체) ──
    diag = repo_root / ".claude" / "self" / "last_diagnosis.json"
    if diag.exists():
        try:
            data = json.loads(diag.read_text(encoding="utf-8"))
            agg = data.get("aggregate", {})
            ok = agg.get("ok", 0)
            warn = agg.get("warn", 0)
            crit = agg.get("critical", 0)
            overall = agg.get("overall", "?")
            summary_line = f"[health] {ok} OK · {warn} WARN · {crit} CRITICAL (overall {overall})"
            blocks.append(_heading3_block(f"System Health — {summary_line}"))
            for r in data.get("results", []):
                name = r.get("name", "?")
                status = r.get("status", "?")
                msg = r.get("message", "") or r.get("value", "")
                icon = "🟢" if status == "OK" else ("🔴" if status == "CRITICAL" else "🟡")
                blocks.append(_bullet_block(f"{icon} {name} — {msg}"[:180]))
        except Exception as e:
            blocks.append(_bullet_block(f"(diagnose.json 파싱 실패: {e})"))
    else:
        health_file = repo_root / ".claude" / "self" / "summary.txt"
        if health_file.exists():
            try:
                line = health_file.read_text(encoding="utf-8").strip().splitlines()[0]
                blocks.append(_heading3_block("System Health"))
                blocks.append(_bullet_block(line[:180]))
            except Exception:
                pass

    # ── 핵심 지표 ──
    blocks.append(_heading3_block("핵심 지표"))
    last = snap.get("last_updated") or "(미기록)"
    sha = snap.get("github_sha_short") or "(미기록)"
    hooks_r = snap.get("hooks_raw", 0)
    hooks_a = snap.get("hooks_active", 0)
    cmds = snap.get("commands", 0)
    smoke = snap.get("smoke") or "unknown"
    blocks.append(_bullet_block(f"최종 업데이트: {last}"))
    blocks.append(_bullet_block(f"GitHub 동기화: commit {sha}"))
    blocks.append(_bullet_block(f"훅 시스템: {hooks_r}개 (raw) / {hooks_a}개 (활성 추정)"))
    blocks.append(_bullet_block(f"슬래시 커맨드: {cmds}개"))
    blocks.append(_bullet_block(f"smoke_test: {smoke}"))

    # ── Circuit Breaker 상태 (Self-X Layer 4) ──
    cb = repo_root / ".claude" / "self" / "circuit_breaker.json"
    if cb.exists():
        try:
            data = json.loads(cb.read_text(encoding="utf-8"))
            st = data.get("state", {})
            th = data.get("thresholds", {})
            locked = st.get("locked", False)
            lock_icon = "🔒" if locked else "🔓"
            lock_reason = st.get("locked_reason", "") or "정상"
            trip_count = st.get("tripped_count_24h", 0)
            blocks.append(_heading3_block(f"Circuit Breaker {lock_icon}"))
            blocks.append(_bullet_block(f"상태: {'잠김' if locked else '정상'} ({lock_reason})"))
            blocks.append(_bullet_block(f"24h trip 카운트: {trip_count}"))
            blocks.append(_bullet_block(
                f"일일 한도: T1 {th.get('daily_t1_limit', '?')} / T2 {th.get('daily_t2_limit', '?')}"
            ))
        except Exception:
            pass

    # ── 최근 Self-Recovery (Layer 2 T1) ──
    recs = _recent_auto_recovery(repo_root, 5)
    if recs:
        blocks.append(_heading3_block(f"최근 Self-Recovery ({len(recs)}건)"))
        for r in recs:
            blocks.append(_bullet_block(r[:180]))

    # ── Incident 상위 kind (최근 7일 미해결) ──
    top_kinds = _incident_top_kinds(repo_root, days=7, top=8)
    if top_kinds:
        total = sum(c for _, c in top_kinds)
        blocks.append(_heading3_block(f"미해결 Incident 상위 (최근 7일, 표시 {total}건)"))
        for kind, count in top_kinds:
            blocks.append(_bullet_block(f"{kind}: {count}건"))

    # ── 최근 커밋 ──
    commits = _recent_commits(repo_root, 10)
    if commits:
        blocks.append(_heading3_block(f"최근 커밋 ({len(commits)}건)"))
        for c in commits:
            blocks.append(_bullet_block(c[:200]))

    return blocks


def _parse_tasks_sections(repo_root: Path) -> dict:
    """TASKS.md 진행/대기/완료 섹션 파싱 (상세 이름 + 차단 사유)."""
    tasks = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    if not tasks.exists():
        return {"progress": [], "pending": [], "completed": []}
    result = {"progress": [], "pending": [], "completed": []}
    section = ""
    try:
        for line in tasks.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("## 진행 중"):
                section = "progress"
            elif s.startswith("## 대기 중"):
                section = "pending"
            elif s.startswith("## 완료됨") or s.startswith("## 최근 완료"):
                section = "completed"
            elif s.startswith("## "):
                section = ""
            elif section and s.startswith("### ") and "~~" not in s:
                name = s.lstrip("# ").strip()[:180]
                result[section].append(name)
    except Exception:
        pass
    # 완료 항목은 최근 30건만
    result["completed"] = result["completed"][:30]
    return result


def _build_tasks_blocks(snap: dict, repo_root: Path) -> list[dict]:
    """TASKS (Auto) 페이지 — 작업 목록 중심.

    포함: 진행/대기/완료 요약 + 세션별 완료 상세 toggle
    제외: 시스템 건강 지표 (STATUS 페이지에서 담당)
    """
    blocks = [
        _text_block(SYNC_EDIT_WARNING),
        _text_block(f"자동 갱신: {snap.get('generated_at', '')}"),
        _divider_block(),
    ]

    sections = _parse_tasks_sections(repo_root)

    blocks.append(_heading3_block("작업 요약"))
    blocks.append(_bullet_block(f"진행 중: {len(sections['progress'])}건"))
    blocks.append(_bullet_block(f"대기 중: {len(sections['pending'])}건"))
    blocks.append(_bullet_block(f"완료(최근): {len(sections['completed'])}건"))

    if sections["progress"]:
        blocks.append(_heading3_block("진행 중"))
        for name in sections["progress"][:15]:
            blocks.append(_bullet_block(name))
    if sections["pending"]:
        blocks.append(_heading3_block("대기 중"))
        for name in sections["pending"][:15]:
            blocks.append(_bullet_block(name))

    # 세션별 완료 상세 (toggleable heading)
    sessions_detail = snap.get("sessions_detail", [])
    all_sess = snap.get("all_sessions", [])
    if sessions_detail:
        blocks.append(_heading3_block(
            f"세션별 완료 이력 (최근 {len(sessions_detail)}건 상세 / 전체 {len(all_sess)}건)"
        ))
        for s in sessions_detail:
            header = s.get("header", "")[:180]
            body = s.get("body", [])
            toggle_block = {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": header}}],
                    "is_toggleable": True,
                    "children": [_bullet_block(b) for b in body] if body else [_text_block("(세부 내용 없음)")]
                }
            }
            blocks.append(toggle_block)

    if all_sess and len(all_sess) > len(sessions_detail):
        blocks.append(_heading3_block(f"전체 세션 헤더 목록 ({len(all_sess)}건)"))
        for s in all_sess:
            blocks.append(_bullet_block(s[:180]))

    return blocks


# 호환 wrapper (기존 sync_update_zone 호출 유지용) — page_type 기본값 "status"
def _snapshot_to_blocks(snap: dict, page_type: str = "status",
                        repo_root: Path | None = None) -> list[dict]:
    """snapshot → Notion 블록. page_type: 'status' | 'tasks'."""
    if repo_root is None:
        repo_root = Path(__file__).parent.parent.parent
    if page_type == "tasks":
        return _build_tasks_blocks(snap, repo_root)
    return _build_status_blocks(snap, repo_root)


def _find_marker_block_ids(page_id: str, token: str,
                            logger: logging.Logger = None) -> tuple[str | None, str | None, list[str]]:
    """SYNC_START / SYNC_END marker block_id 반환.

    반환: (start_id, end_id, zone_inner_ids)
    marker 중 하나라도 없으면 (None, None, []) 반환 — 호출자가 재생성.
    """
    blocks = _get_page_blocks(page_id, token)
    start_id = None
    end_id = None
    zone_inner_ids: list[str] = []
    state = "before_start"

    for b in blocks:
        btype = b.get("type", "")
        text = ""
        if btype == "paragraph":
            rich = b.get("paragraph", {}).get("rich_text", [])
            text = "".join(r.get("plain_text", "") for r in rich)
        if state == "before_start":
            if SYNC_MARKER_START in text:
                start_id = b["id"]
                state = "in_zone"
            continue
        if state == "in_zone":
            if SYNC_MARKER_END in text:
                end_id = b["id"]
                state = "after_end"
                break
            zone_inner_ids.append(b["id"])

    if not start_id or not end_id:
        return None, None, []
    return start_id, end_id, zone_inner_ids


def _create_sync_markers(page_id: str, token: str,
                          logger: logging.Logger = None) -> tuple[str | None, str | None]:
    """SYNC_START/END marker 블록을 STATUS 페이지 최상단에 생성.

    반환: (start_id, end_id). 실패 시 (None, None).

    구현: 페이지 children에 SYNC_START paragraph + SYNC_END paragraph를 append.
    기존 첫 블록 위로 올리려면 `after` 없이 append하면 뒤에 추가됨 — Notion API는
    block children append가 맨 뒤에만 들어가므로 "최상단" 요구는 heading을 따로 둔다.
    타협: marker는 페이지 끝에 생성되어도 덮어쓰기 대상은 내부 영역이므로 기능상 OK.
    사용자가 수동으로 marker 블록을 페이지 상단으로 드래그해 재배치 가능.
    """
    pid = page_id.replace("-", "")
    # marker만 생성 (warning은 snapshot_to_blocks에서 zone 내부에 삽입)
    marker_blocks = [
        _text_block(SYNC_MARKER_START),
        _text_block(SYNC_MARKER_END),
    ]
    result = _notion_request(
        "PATCH", f"/blocks/{pid}/children", token,
        {"children": marker_blocks}, logger=logger
    )
    if not result:
        return None, None
    added = result.get("results", [])
    if len(added) < 2:
        return None, None
    start_id = added[0].get("id")
    end_id = added[-1].get("id")
    if logger:
        logger.info(f"SYNC marker 생성: start={start_id} end={end_id}")
    return start_id, end_id


def _update_legacy_header_lines(page_id: str, snap: dict, token: str,
                                 logger: logging.Logger = None) -> bool:
    """STATUS 페이지 상단 legacy 텍스트 라인을 snapshot 값으로 덮어쓰기.

    대상 3라인 (정규식 매칭 첫 발견):
    - "최종 업데이트: YYYY-MM-DD — 세션NN ..."
    - "GitHub 동기화: YYYY-MM-DD / commit XXXXXX"
    - "원본: Git/TASKS.md 기준 | 동기화: YYYY-MM-DD"

    세션88 3way 합의 이후 사용자 지적("제목은 세션88인데 본문은 세션45") 해소용.
    SYNC zone은 하단 생성 (Notion API 제약)이므로 상단 legacy 라인도 최신화 필요.
    """
    blocks = _get_page_blocks(page_id, token)
    if not blocks:
        return False

    last_updated = snap.get("last_updated") or "(미기록)"
    sha_short = snap.get("github_sha_short") or "(미기록)"
    today = datetime.now().strftime("%Y-%m-%d")

    # 세션 태그에서 "세션NN" 부분만 추출 (중복 날짜 제거)
    session_only = last_updated
    m_sess = _re.match(r"(세션\d+)", last_updated)
    if m_sess:
        session_only = m_sess.group(1)

    # 새 텍스트 라인
    new_last_updated = f"최종 업데이트: {today} — {session_only}"
    new_github_sync = f"GitHub 동기화: {today} / commit {sha_short}"
    new_origin = f"원본: Git/TASKS.md 기준 | 동기화: {today}"

    # 느슨한 매칭: startswith + 키워드 포함 (Notion paragraph 안에 Shift+Enter로 여러 line 있을 가능성 대응)
    patterns = [
        (lambda t: t.startswith("최종 업데이트:") and _re.search(r"\d{4}-\d{2}-\d{2}", t), new_last_updated),
        (lambda t: t.startswith("GitHub 동기화:") and _re.search(r"\d{4}-\d{2}-\d{2}", t), new_github_sync),
        (lambda t: t.startswith("원본:") and "동기화" in t, new_origin),
    ]
    matched = [False] * len(patterns)

    # paragraph + callout + quote 모두 검사 (Notion 본문의 상단 강조 라인은 callout 또는 quote일 수 있음)
    TEXT_BLOCK_TYPES = ("paragraph", "callout", "quote")

    updated = 0
    for b in blocks:
        btype = b.get("type", "")
        if btype not in TEXT_BLOCK_TYPES:
            continue
        rich = b.get(btype, {}).get("rich_text", [])
        text = "".join(r.get("plain_text", "") for r in rich).strip()
        for i, (check, new_text) in enumerate(patterns):
            if matched[i]:
                continue
            if check(text):
                # btype별 payload 구조 — callout/quote도 rich_text 업데이트, icon/color는 보존 생략
                payload = {btype: {
                    "rich_text": [{"type": "text", "text": {"content": new_text}}]
                }}
                result = _notion_request(
                    "PATCH", f"/blocks/{b['id']}", token,
                    payload, logger=logger
                )
                if result:
                    updated += 1
                    matched[i] = True
                break

    if logger:
        logger.info(f"legacy 상단 라인 갱신: {updated}/{len(patterns)}건 매칭")
    return updated > 0


def sync_update_zone(page_id: str, snap: dict, token: str,
                     logger: logging.Logger = None,
                     page_type: str = "status") -> bool:
    """SYNC_START/END 사이 블록을 snapshot 내용으로 덮어쓰기.

    1. marker 찾기. 없으면 자동 재생성.
    2. zone 내부 기존 블록 전부 삭제.
    3. snapshot 블록을 SYNC_END 블록 앞에 삽입 (after=start_id).
       Notion API 제약: `after` 파라미터로 특정 블록 뒤 삽입. SYNC_END 앞에 두려면
       SYNC_START 뒤로 삽입. 이 API는 "after block 뒤"라 end 앞이 되려면
       zone inner가 모두 삭제된 뒤 SYNC_START 뒤에 순차 append → 자동으로 END 앞에 위치.
    """
    if not page_id:
        if logger:
            logger.warning("sync_update_zone: page_id 없음")
        return False

    start_id, end_id, inner_ids = _find_marker_block_ids(page_id, token, logger)

    if not start_id or not end_id:
        # 마커 자동 재생성 (Gemini 제안 반영)
        if logger:
            logger.warning("SYNC marker 없음 — 자동 재생성 시도")
        start_id, end_id = _create_sync_markers(page_id, token, logger)
        if not start_id or not end_id:
            if logger:
                logger.error("SYNC marker 재생성 실패")
            return False
        inner_ids = []

    # zone 내부 기존 블록 삭제
    deleted = 0
    for bid in inner_ids:
        if _delete_block(bid, token, logger):
            deleted += 1
    if logger and inner_ids:
        logger.info(f"SYNC zone 내부 {len(inner_ids)}개 중 {deleted}개 삭제")

    # snapshot 블록 생성 후 SYNC_START 뒤에 삽입 (page_type별 분기)
    new_blocks = _snapshot_to_blocks(snap, page_type=page_type)
    pid = page_id.replace("-", "")
    result = _notion_request(
        "PATCH", f"/blocks/{pid}/children", token,
        {"children": new_blocks, "position": {"type": "after_block", "after_block": {"id": start_id}}},
        logger=logger
    )
    if not result:
        if logger:
            logger.error("SYNC zone 블록 삽입 실패")
        return False
    if logger:
        logger.info(f"SYNC zone {len(new_blocks)}블록 삽입 성공")
    return True


def _parse_session_tag(repo_root: Path) -> str | None:
    """TASKS.md '최종 업데이트: YYYY-MM-DD — 세션NN' 라인에서 제목용 태그 생성.

    반환: "세션86 갱신 2026-04-21" 형식, 실패 시 None.
    """
    tasks_md = repo_root / "90_공통기준" / "업무관리" / "TASKS.md"
    if not tasks_md.exists():
        return None
    try:
        for line in tasks_md.read_text(encoding="utf-8").splitlines()[:30]:
            m = _re.match(r"^최종 업데이트:\s*(\d{4}-\d{2}-\d{2})\s*—\s*(세션\d+)", line)
            if m:
                return f"{m.group(2)} 갱신 {m.group(1)}"
    except Exception:
        return None
    return None


# ── Auto 페이지 자동 생성 (세션88 3way A안) ──────────────────────────────

def _create_auto_page(parent_page_id: str, title: str, token: str,
                       logger: logging.Logger = None) -> str | None:
    """parent_page_id 하위에 자동 동기화 전용 자식 페이지 생성. 반환 page_id.

    Notion API: POST /pages. parent는 page_id. properties.title만 설정.
    생성 직후 페이지 children은 비어있음 → sync_update_zone이 이후 SYNC marker + 블록 생성.
    """
    if not parent_page_id:
        if logger:
            logger.error("parent_page_id 없음 — auto 페이지 생성 불가")
        return None
    pid = parent_page_id.replace("-", "")
    payload = {
        "parent": {"type": "page_id", "page_id": pid},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }
    }
    result = _notion_request("POST", "/pages", token, payload=payload, logger=logger)
    if not result:
        if logger:
            logger.error(f"auto 페이지 생성 실패: title={title}")
        return None
    new_id = result.get("id")
    if logger and new_id:
        logger.info(f"auto 페이지 생성: title='{title}' id={new_id}")
    return new_id


def _ensure_auto_pages(cfg: dict, token: str,
                        logger: logging.Logger = None) -> tuple[str | None, str | None]:
    """auto 페이지 ID 확보. 없으면 생성 + notion_config.yaml 갱신.

    반환: (status_auto_id, tasks_auto_id). 실패 시 None.
    """
    notion_cfg = cfg.get("notion", {})
    status_auto = notion_cfg.get("status_auto_page_id") or ""
    tasks_auto = notion_cfg.get("tasks_auto_page_id") or ""
    parent_id = notion_cfg.get("parent_page_id") or ""

    updated = False

    if not status_auto:
        new_id = _create_auto_page(
            parent_id, "📊 STATUS (Auto) — 자동 운영 현황", token, logger
        )
        if new_id:
            status_auto = new_id
            updated = True
        elif logger:
            logger.error("STATUS (Auto) 페이지 자동 생성 실패 — 수동 생성 후 notion_config.yaml 기입 필요")

    if not tasks_auto:
        new_id = _create_auto_page(
            parent_id, "✅ TASKS (Auto) — 자동 작업 목록", token, logger
        )
        if new_id:
            tasks_auto = new_id
            updated = True
        elif logger:
            logger.error("TASKS (Auto) 페이지 자동 생성 실패 — 수동 생성 후 notion_config.yaml 기입 필요")

    # yaml 영구 기입 (다음 실행부터 재사용)
    if updated:
        try:
            cfg_path = CONFIG_PATH
            content = cfg_path.read_text(encoding="utf-8")
            # 라인 말미 preserve (개행 손실 방지)
            content = _re.sub(
                r'(status_auto_page_id:\s*)"[^"]*"',
                lambda m: f'{m.group(1)}"{status_auto}"',
                content,
            )
            content = _re.sub(
                r'(tasks_auto_page_id:\s*)"[^"]*"',
                lambda m: f'{m.group(1)}"{tasks_auto}"',
                content,
            )
            cfg_path.write_text(content, encoding="utf-8")
            # in-memory cfg도 갱신 (이번 실행 내 재사용)
            cfg["notion"]["status_auto_page_id"] = status_auto
            cfg["notion"]["tasks_auto_page_id"] = tasks_auto
            if logger:
                logger.info(f"notion_config.yaml auto_page_id 기입 완료")
        except Exception as e:
            if logger:
                logger.error(f"notion_config.yaml 갱신 예외: {e}")

    return (status_auto or None, tasks_auto or None)


def update_page_title(page_id: str, new_title: str, token: str,
                      logger: logging.Logger = None) -> bool:
    """Notion 페이지 제목 갱신. PATCH /pages/{page_id}.

    세션86 오후 별건 추가: notion_sync가 요약 블록만 갱신하고 페이지 제목은
    세션45 상태로 남아 있던 드리프트를 해소.
    """
    if not page_id:
        return True  # 설정 없음 = 대상 없음 (성공 간주)
    body = {
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": new_title}}]
            }
        }
    }
    result = _notion_request("PATCH", f"/pages/{page_id}", token,
                             payload=body, logger=logger)
    if result is None:
        if logger:
            logger.error(f"페이지 제목 갱신 실패: page_id={page_id}")
        return False
    return True


# ── /finish 4.5단계 실운영 wrapper (세션86 3자 토론 채택, GPT 조건부 통과 보정) ──

def sync_from_finish(cfg: dict = None, logger: logging.Logger = None) -> bool:
    """/finish 4.5단계 수동 동기화 전용 wrapper.

    설계 (세션86 3자 토론):
    - events 없이 STATUS 요약(update_summary) + 부모 페이지(sync_parent_page)만 갱신
    - sync_batch/_mark_done/dedup 로직 완전 우회 — 허위 이력 append 방지 (GPT 지적)
    - 실패 soft-fail — 부분 성공도 True 반환하지 않음. 호출자(finish.md)가 `|| true`로 감싸 non-blocking
    """
    if cfg is None:
        cfg = load_config()
    if logger is None:
        logger = setup_error_logger(cfg)
    token = load_token(cfg)
    if not token:
        logger.error("Notion 토큰 없음 — NOTION_TOKEN 환경변수 또는 .env 확인")
        return False
    repo_root = Path(__file__).parent.parent.parent

    ok_summary = False
    try:
        ok_summary = update_summary(token, cfg, repo_root, logger)
    except Exception as e:
        logger.error(f"update_summary 예외: {e}")

    ok_parent = False
    try:
        ok_parent = sync_parent_page(token, cfg, repo_root, logger)
    except Exception as e:
        logger.error(f"sync_parent_page 예외: {e}")

    # 세션88 3way A안: auto 페이지 대상으로 전환. legacy regex 땜질 제거.
    # 기존 status_page_id / tasks_page_id는 historical 보존(건드리지 않음).

    # Auto 페이지 ID 확보 (없으면 자동 생성)
    status_auto_pid, tasks_auto_pid = _ensure_auto_pages(cfg, token, logger)

    # SYNC zone 갱신 + snapshot.json 저장
    ok_zone = True
    ok_snap_json = True
    snap = None
    try:
        snap = generate_snapshot(repo_root)
        ok_snap_json = write_snapshot_json(snap, logger)

        for pid_name, pid, ptype in [
            ("STATUS(Auto)", status_auto_pid, "status"),
            ("TASKS(Auto)", tasks_auto_pid, "tasks"),
        ]:
            if not pid:
                ok_zone = False
                if logger:
                    logger.error(f"{pid_name} page_id 없음 — SYNC zone 갱신 불가")
                continue
            ok_page = sync_update_zone(pid, snap, token, logger, page_type=ptype)
            ok_zone = ok_zone and ok_page
    except Exception as e:
        ok_zone = False
        if logger:
            logger.error(f"SYNC zone 갱신 예외: {e}")

    # Auto 페이지 제목 갱신 (세션 경계 감지)
    ok_titles = True
    try:
        session_tag = _parse_session_tag(repo_root)
        if session_tag:
            tag_cache = Path(__file__).parent / ".notion_last_session_tag"
            prev_tag = ""
            if tag_cache.exists():
                try:
                    prev_tag = tag_cache.read_text(encoding="utf-8").strip()
                except Exception:
                    prev_tag = ""
            if prev_tag == session_tag:
                if logger:
                    logger.info(f"세션 태그 동일({session_tag}) — 제목 갱신 스킵")
            else:
                if status_auto_pid:
                    ok_s = update_page_title(
                        status_auto_pid,
                        f"📊 STATUS (Auto) — 자동 운영 현황 ({session_tag})",
                        token, logger
                    )
                    ok_titles = ok_titles and ok_s
                if tasks_auto_pid:
                    ok_t = update_page_title(
                        tasks_auto_pid,
                        f"✅ TASKS (Auto) — 자동 작업 목록 ({session_tag})",
                        token, logger
                    )
                    ok_titles = ok_titles and ok_t
                if logger:
                    logger.info(f"auto 페이지 제목 태그 갱신: {session_tag} (ok={ok_titles})")
                if ok_titles:
                    try:
                        tag_cache.write_text(session_tag, encoding="utf-8")
                    except Exception:
                        pass
        elif logger:
            logger.warning("TASKS.md 최종 업데이트 라인 파싱 실패 — 제목 갱신 스킵")
            ok_titles = False
    except Exception as e:
        ok_titles = False
        if logger:
            logger.error(f"auto 제목 갱신 예외: {e}")

    return ok_summary and ok_parent and ok_titles and ok_zone and ok_snap_json


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 5 Notion 동기화")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-id", default="test1234")
    parser.add_argument("--manual-sync", action="store_true",
                        help="/finish 4.5단계 수동 동기화 (events 없이 요약+부모만 갱신)")
    args = parser.parse_args()

    cfg    = load_config()
    logger = setup_error_logger(cfg)

    if args.manual_sync:
        ok = sync_from_finish(cfg, logger)
        print("Notion 수동 동기화 성공" if ok else "Notion 수동 동기화 실패")
        sys.exit(0 if ok else 1)

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
