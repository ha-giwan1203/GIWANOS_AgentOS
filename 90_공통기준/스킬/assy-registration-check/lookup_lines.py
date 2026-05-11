"""
모품번 리스트 → ERP 조립비 현황관리(New) 컬러별 라인 등록 일괄 조회.

erp_lookup.py(기존)는 PROD_NO 1건당 Dtl API만 호출 — 컬러 포함 13자리 가정.
본 wrapper는 모품번(10자리) 입력 시 Hdr API → 컬러별 N건 → 컬러별 Dtl API 합성.

흐름:
    모품번 → Hdr API(searchProdNo prefix LIKE) → 컬러별 N행
    각 컬러 PROD_NO → Dtl API → 라인 등록 N행
    → {모품번: {colors: [...], lines_by_color: {컬러: [라인행]}, raw_hdr: [...]}}

기존 erp_lookup.py의 internal 함수 직접 import (CDP/OAuth/iframe 진입/blackout 회피 동일).
"""
import json
import sys
import time
from pathlib import Path

# erp_lookup.py 직접 import (sibling skill)
ERP_LOOKUP_DIR = Path(__file__).resolve().parent.parent / "gerp-unregistered-check"
sys.path.insert(0, str(ERP_LOOKUP_DIR))
import erp_lookup  # noqa


def lookup_root_pns_with_colors(pns_root, appl_da, cmpy_cd="0109"):
    """
    Args:
        pns_root: 모품번 리스트 (10자리, 컬러코드 없음). 13자리 컬러품번도 동작 가능 (Hdr이 prefix LIKE 매칭).
        appl_da: 적용일 (YYYY-MM-DD)
        cmpy_cd: 업체코드. **Hdr 단계엔 적용 안 함** (사용자 ERP 검색이 조립업체 빈칸이므로). Dtl 결과에 ASSY_CMPY_CD가 있어 분류 단계에서 필터링. 호환성 위해 인자 유지.
    Returns:
        {
          모품번: {
            "colors": ["89880DO510EFD", ...],     # PROD_NO 13자리
            "lines_by_color": {
              "89880DO510EFD": [{"ASSY_LINE_CD": "SP3M3", "ASSY_CMPY_CD": "0109", ...}, ...],
              ...
            },
            "raw_hdr": [...],                      # Hdr API raw 응답
            "error": str or None,
          }
        }
    """
    print(f"=== ERP 라인 등록 일괄 조회 (모품번 {len(pns_root)}개 / 적용일 {appl_da}) ===")

    erp_lookup.ensure_chrome_cdp()
    try:
        erp_lookup.ensure_erp_login_via_playwright()
    except Exception as e:
        print(f"[phase0] OAuth 처리 (이미 로그인일 수 있음): {e}")

    if not erp_lookup._try_open_assy_menu():
        raise RuntimeError("조립비 현황관리(New) iframe 진입 실패")

    ws, ctx_id = erp_lookup._connect_assy_iframe()
    print(f"[CDP] context_id={ctx_id}")

    result = {}
    err_count = 0
    for i, root in enumerate(pns_root):
        erp_lookup.wait_sync_clear()
        entry = {"colors": [], "lines_by_color": {}, "raw_hdr": None, "error": None}

        # 1. Hdr API — 모품번 prefix LIKE 검색 → 컬러별 N건 (업체 필터 없음 — 사용자 ERP 검색 동일)
        try:
            hdr = erp_lookup.fetch_pn_hdr(
                ws, root, appl_da, cmpy_cd="",
                msg_id=2000 + i, context_id=ctx_id,
            )
        except Exception as e:
            entry["error"] = f"Hdr exception: {e}"
            result[root] = entry
            err_count += 1
            time.sleep(1)
            continue

        if hdr is None:
            entry["error"] = "Hdr API 실패"
            result[root] = entry
            err_count += 1
            continue

        entry["raw_hdr"] = hdr
        # PROD_NO 컬럼 추출 (컬러별 unique)
        colors = []
        seen = set()
        for h in hdr:
            pn = (h.get("PROD_NO") or h.get("PRODUCT_NO") or "").strip()
            if pn and pn not in seen:
                seen.add(pn)
                colors.append(pn)
        entry["colors"] = colors

        # 2. 컬러별 Dtl API
        for j, color_pn in enumerate(colors):
            erp_lookup.wait_sync_clear()
            try:
                dtl = erp_lookup.fetch_pn_lines(
                    ws, color_pn, appl_da,
                    msg_id=3000 + i * 100 + j, context_id=ctx_id,
                )
            except Exception as e:
                entry["lines_by_color"][color_pn] = []
                if entry["error"] is None:
                    entry["error"] = f"Dtl exception ({color_pn}): {e}"
                continue
            entry["lines_by_color"][color_pn] = dtl or []
            time.sleep(erp_lookup.DELAY_SEC)

        result[root] = entry
        if (i + 1) % 10 == 0 or (i + 1) == len(pns_root):
            n_colors = sum(len(v["colors"]) for v in result.values())
            print(f"  [{i+1}/{len(pns_root)}] {root} colors={len(colors)} 누적컬러={n_colors}")
        time.sleep(erp_lookup.DELAY_SEC)

    try:
        ws.close()
    except Exception:
        pass

    print(f"\n[DONE] 모품번 {len(result)} / 에러 {err_count}")
    return result


if __name__ == "__main__":
    # 단독 실행 — 모품번 1건 테스트
    test = ["89880DO510"]
    r = lookup_root_pns_with_colors(test, appl_da="2026-05-09")
    print(json.dumps(r, ensure_ascii=False, indent=2))
