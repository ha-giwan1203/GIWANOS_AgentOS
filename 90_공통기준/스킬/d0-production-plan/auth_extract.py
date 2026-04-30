"""auth_extract.py — 옵션 A 하이브리드 P1 PoC

세션131 사용자 명시 P1 진입 (2026-04-30).
PLAN_API_HYBRID.md P1 단계 — read-only 검증만.

목적:
  Playwright OAuth 로그인 세션에서 cookie/XSRF 후보를 추출하고,
  requests로 dev ERP GET 1회만 호출해 200 응답 여부를 확인한다.

P1 안전장치 (사용자 명시 금지 사항 준수):
  - POST 호출 금지 (dry_run = True 기본)
  - selectListPmD0AddnUpload / multiList / rank / MES / DELETE 모두 호출 금지
  - run.py / bat 미수정
  - 운영 URL 미호출 — erp-dev.samsong.com 한정
  - 재시도 루프 없음 (실패 시 원인만 기록)
  - 쿠키 값 전체 출력 금지 (이름 목록만)
  - XSRF 앞뒤 4자리만 마스킹 표시

사용 예:
  python auth_extract.py
  → 결과: stdout JSON + log file 06_생산관리/D0_업로드/logs/api_poc_p1_YYYYMMDD_HHMMSS.log
"""
import sys, os, json, time
from datetime import datetime
from pathlib import Path

# cp949 콘솔 호환 (Windows 작업 스케줄러 호출 가능성)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 외부 라이브러리
try:
    from playwright.sync_api import sync_playwright
    import requests
except Exception as e:
    print(f"[FAIL] dependency import: {e}", file=sys.stderr)
    sys.exit(2)

# run.py의 OAuth 자동 로그인 함수 재사용 (SKILL.md Phase 0 절차 준수, 세션131 보강)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from run import ensure_erp_login, _wait_oauth_complete, _safe_goto, D0_URL as RUN_D0_URL
except Exception as e:
    print(f"[FAIL] run.py import: {e}", file=sys.stderr)
    sys.exit(2)

# ===== 설정 (run.py와 동일 — dev 환경만) =====
CDP_URL = "http://127.0.0.1:9223"
ERP_LAYOUT = "http://erp-dev.samsong.com:19100/layout/layout.do"  # GET 대상
D0_URL = "http://erp-dev.samsong.com:19100/prdtPlanMng/viewListDoAddnPrdtPlanInstrMngNew.do"  # 세션 확보용 진입
LOG_DIR = Path("06_생산관리/D0_업로드/logs")
TIMEOUT = 10  # requests timeout 10s, 재시도 없음


def mask_token(value: str) -> str:
    """XSRF 토큰 마스킹 — 앞 4 + ... + 뒤 4."""
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]} (len={len(value)})"


def cdp_alive(url: str) -> bool:
    """CDP 활성 확인 — read-only ping."""
    try:
        import urllib.request
        urllib.request.urlopen(f"{url}/json/version", timeout=3)
        return True
    except Exception:
        return False


def extract_xsrf_candidates(page, cookies_list) -> dict:
    """XSRF 후보 4개 실측 — page DOM + cookies."""
    out = {"cookie_xsrf_token": None, "ajax_settings_headers": None, "meta_xsrf": None, "hidden_csrf_input": None}

    # (a) cookie XSRF-TOKEN
    for c in cookies_list:
        if c.get("name", "").upper() in ("XSRF-TOKEN", "X-XSRF-TOKEN"):
            out["cookie_xsrf_token"] = c.get("value")
            break

    # (b) jQuery $.ajaxSettings.headers
    try:
        out["ajax_settings_headers"] = page.evaluate(
            "() => { try { return JSON.stringify($.ajaxSettings.headers || {}); } catch(e) { return null; } }"
        )
    except Exception as e:
        out["ajax_settings_headers"] = f"(eval error: {type(e).__name__})"

    # (c) meta[name=XSRF-TOKEN]
    try:
        out["meta_xsrf"] = page.evaluate(
            "() => { const m = document.querySelector('meta[name=\"XSRF-TOKEN\"], meta[name=\"_csrf\"], meta[name=\"csrf-token\"]'); return m ? m.content : null; }"
        )
    except Exception as e:
        out["meta_xsrf"] = f"(eval error: {type(e).__name__})"

    # (d) hidden input[name=_csrf] 또는 input[name=XSRF-TOKEN]
    try:
        out["hidden_csrf_input"] = page.evaluate(
            "() => { const i = document.querySelector('input[name=\"_csrf\"], input[name=\"XSRF-TOKEN\"], input[name=\"csrf_token\"]'); return i ? i.value : null; }"
        )
    except Exception as e:
        out["hidden_csrf_input"] = f"(eval error: {type(e).__name__})"

    return out


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"api_poc_p1_{ts}.log"
    result = {
        "started_at": datetime.now().isoformat(),
        "cdp_url": CDP_URL,
        "target_get": ERP_LAYOUT,
        "phase": "P1",
        "dry_run": True,
        "post_blocked": True,
    }

    # CDP alive check
    if not cdp_alive(CDP_URL):
        result["status"] = "CDP_DEAD"
        result["error"] = f"{CDP_URL} 미응답. 사용자 manual launch 후 재실행 필요."
        result["hint"] = "Start-Process chrome.exe -ArgumentList '--remote-debugging-port=9223','--remote-debugging-address=127.0.0.1','--user-data-dir=C:\\Users\\User\\.flow-chrome-debug'"
        log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # Playwright connect + extract
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            ctx = browser.contexts[0]
            # 기존 D0 화면 탭 또는 ERP 도메인 탭 확보
            page = None
            for pg in ctx.pages:
                if "erp-dev.samsong.com" in pg.url or "auth-dev.samsong.com" in pg.url:
                    page = pg
                    break
            if page is None:
                # ERP 도메인 탭이 없으면 새 탭 — D0_URL 진입은 OAuth 필요 가능성, layout만 GET 시도
                page = ctx.new_page()
                page.goto(ERP_LAYOUT, timeout=15000)
                time.sleep(2)

            page.bring_to_front()
            result["page_url_initial"] = page.url

            # SKILL.md Phase 0 절차 준수: ensure_erp_login + _wait_oauth_complete (세션131 보강)
            try:
                ensure_erp_login(page)
                oauth_ok = _wait_oauth_complete(page, timeout_sec=60.0)
                result["oauth_completed"] = oauth_ok
                if not oauth_ok and "auth-dev.samsong.com" in page.url:
                    # 1회 재시도 + D0_URL 직접 이동
                    _safe_goto(page, RUN_D0_URL)
                    oauth_ok = _wait_oauth_complete(page, timeout_sec=60.0)
                    result["oauth_completed_retry"] = oauth_ok
            except Exception as e:
                result["oauth_error"] = f"{type(e).__name__}: {str(e)[:200]}"

            result["page_url_before_extract"] = page.url

            # cookies 추출 (이름 목록만 — 사용자 명시 마스킹 준수)
            cookies_list = ctx.cookies()
            result["cookie_count"] = len(cookies_list)
            result["cookie_names"] = sorted({c["name"] for c in cookies_list})
            result["cookie_domains"] = sorted({c.get("domain", "") for c in cookies_list})

            # XSRF 후보 4개
            xsrf = extract_xsrf_candidates(page, cookies_list)
            result["xsrf_candidates"] = {
                "cookie_xsrf_token": mask_token(xsrf["cookie_xsrf_token"]) if xsrf["cookie_xsrf_token"] else None,
                "ajax_settings_headers": xsrf["ajax_settings_headers"],
                "meta_xsrf": mask_token(xsrf["meta_xsrf"]) if xsrf["meta_xsrf"] else None,
                "hidden_csrf_input": mask_token(xsrf["hidden_csrf_input"]) if xsrf["hidden_csrf_input"] else None,
            }

            # requests.Session 구성 — cookies 동봉
            sess = requests.Session()
            for c in cookies_list:
                domain = c.get("domain", "")
                if "samsong.com" not in domain:
                    continue
                sess.cookies.set(
                    name=c["name"], value=c["value"],
                    domain=domain.lstrip("."), path=c.get("path", "/"),
                )
            # XSRF 헤더 동봉 (cookie 출처 우선, 그 다음 meta)
            chosen_xsrf = xsrf["cookie_xsrf_token"] or xsrf["meta_xsrf"] or xsrf["hidden_csrf_input"]
            if chosen_xsrf and not str(chosen_xsrf).startswith("(eval"):
                sess.headers.update({"X-XSRF-TOKEN": chosen_xsrf, "XSRF-TOKEN": chosen_xsrf})
                result["xsrf_chosen_source"] = (
                    "cookie" if xsrf["cookie_xsrf_token"]
                    else "meta" if xsrf["meta_xsrf"]
                    else "hidden_input"
                )
            else:
                result["xsrf_chosen_source"] = "none"

            # **GET 1회만** — POST/multiList/rank/MES/DELETE 절대 호출 금지
            t0 = time.time()
            r = sess.get(ERP_LAYOUT, timeout=TIMEOUT, allow_redirects=True)
            elapsed_ms = int((time.time() - t0) * 1000)

            result["http_status"] = r.status_code
            result["http_elapsed_ms"] = elapsed_ms
            result["http_final_url"] = r.url
            result["http_redirect_chain"] = [
                {"status": h.status_code, "url": h.url} for h in r.history
            ]
            result["http_html_length"] = len(r.text)
            result["http_content_type"] = r.headers.get("Content-Type", "")

            # 판정 라벨 (재시도 없이 단발)
            if r.status_code == 200:
                result["verdict"] = "P1_PASS_GET_200"
            elif r.status_code in (302, 303, 307, 308):
                result["verdict"] = "P1_REDIRECT_AUTH_NEEDED"
            elif r.status_code == 401 or r.status_code == 403:
                result["verdict"] = "P1_AUTH_REJECTED"
            elif r.status_code == 500:
                result["verdict"] = "P1_SERVER_500_LIKELY_XSRF"
            else:
                result["verdict"] = f"P1_UNEXPECTED_{r.status_code}"

            result["status"] = "DONE"

    except Exception as e:
        result["status"] = "EXCEPTION"
        result["exception_type"] = type(e).__name__
        result["exception_msg"] = str(e)[:300]

    result["finished_at"] = datetime.now().isoformat()
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n[INFO] log: {log_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
