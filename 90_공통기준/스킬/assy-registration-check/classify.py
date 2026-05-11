"""
모품번별 ERP 조회 결과 → 분류.

입력:
    rows = [{"pn": str, "exempt": bool, "차종": str, ...}, ...]   # 마스터 추출
    erp_result = {pn: {colors, lines_by_color, raw_hdr, error}}    # lookup_lines 산출
    primary, paired = "SP3M3", "HCAMS02"

출력:
    {
      "정상_일반": [...],
      "primary누락_일반": [...],
      "paired누락_일반": [...],
      "양쪽누락_일반": [...],
      "미등록_일반": [...],
      "정상_면제": [...],
      "primary누락_면제": [...],
      "미등록_면제": [...],
      "이상_면제paired등록": [...],
      "컬러편차": [...],     # 별도 — 위 분류와 중복 가능
    }
"""
from collections import defaultdict


CATEGORIES = [
    "정상_일반",
    "primary누락_일반",
    "paired누락_일반",
    "양쪽누락_일반",
    "미등록_일반",
    "정상_면제",
    "primary누락_면제",
    "미등록_면제",
    "이상_면제paired등록",
    "컬러편차",
]


TARGET_CMPY_CD = "0109"  # 대원테크 (정산 대상 업체)


def _line_set_per_color(lines_by_color):
    """컬러별 라인코드 set — 0109 업체 등록만 카운트."""
    out = {}
    for c, rows in lines_by_color.items():
        s = set()
        for r in rows:
            line = (r.get("ASSY_LINE_CD") or "").strip()
            cmpy = (r.get("ASSY_CMPY_CD") or "").strip()
            if line and cmpy == TARGET_CMPY_CD:
                s.add(line)
        out[c] = s
    return out


def _has_any_registration(lines_by_color):
    """모품번 자체 ERP 등록 존재 여부 — 업체 무관, 전체 행 합 1+ ."""
    for rows in lines_by_color.values():
        if rows:
            return True
    return False


def classify(rows, erp_result, primary_cd, paired_cd):
    out = {k: [] for k in CATEGORIES}

    for row in rows:
        pn = row["pn"]
        exempt = bool(row.get("exempt"))
        entry = erp_result.get(pn) or {"colors": [], "lines_by_color": {}, "raw_hdr": None, "error": "조회결과없음"}

        colors = entry.get("colors", [])
        lines_by_color = entry.get("lines_by_color", {})
        per_color = _line_set_per_color(lines_by_color)

        # 모품번 합집합
        all_lines = set()
        for s in per_color.values():
            all_lines |= s

        has_primary = primary_cd in all_lines
        has_paired = paired_cd in all_lines if paired_cd else False
        # "품번 자체 미등록" = ERP에 0109 한정으로 어떤 라인도 등록 0건
        # (Hdr 컬러 0건이거나 컬러 있어도 0109 라인 0건)
        no_registration = (len(colors) == 0) or (len(all_lines) == 0)

        # 컬러 편차 — 컬러별로 primary 또는 paired 등록 여부가 일치하지 않을 때
        primary_per_color = {c: (primary_cd in s) for c, s in per_color.items()}
        if primary_per_color and len(set(primary_per_color.values())) > 1:
            # 일부 컬러만 primary 등록
            row_with_diag = dict(row)
            row_with_diag["_diag"] = f"primary({primary_cd}) 컬러편차: " + ", ".join(
                f"{c}={'O' if v else 'X'}" for c, v in primary_per_color.items()
            )
            row_with_diag["colors"] = ",".join(colors)
            out["컬러편차"].append(row_with_diag)
        if paired_cd and per_color:
            paired_per_color = {c: (paired_cd in s) for c, s in per_color.items()}
            if paired_per_color and len(set(paired_per_color.values())) > 1 and not exempt:
                row_with_diag = dict(row)
                row_with_diag["_diag"] = f"paired({paired_cd}) 컬러편차: " + ", ".join(
                    f"{c}={'O' if v else 'X'}" for c, v in paired_per_color.items()
                )
                row_with_diag["colors"] = ",".join(colors)
                # 같은 row가 primary·paired 양쪽 편차일 수 있음 — 중복 추가 허용 (시트에서 사용자 확인)
                if not any(r["pn"] == pn and "paired" in r.get("_diag", "") for r in out["컬러편차"]):
                    out["컬러편차"].append(row_with_diag)

        # 메인 분류
        annotated = dict(row)
        annotated["all_lines"] = ",".join(sorted(all_lines))
        annotated["colors_n"] = len(colors)

        if exempt:
            if no_registration:
                out["미등록_면제"].append(annotated)
            elif not has_primary:
                out["primary누락_면제"].append(annotated)
            elif has_paired:
                out["이상_면제paired등록"].append(annotated)
            else:
                out["정상_면제"].append(annotated)
        else:
            if no_registration:
                out["미등록_일반"].append(annotated)
            elif has_primary and has_paired:
                out["정상_일반"].append(annotated)
            elif has_primary and not has_paired:
                out["paired누락_일반"].append(annotated)
            elif not has_primary and has_paired:
                out["primary누락_일반"].append(annotated)
            else:
                out["양쪽누락_일반"].append(annotated)

    return out


def summarize(classified):
    """분류별 건수."""
    summary = {}
    for k, v in classified.items():
        summary[k] = len(v)
    summary["__total_main__"] = sum(
        v for k, v in summary.items()
        if not k.startswith("__") and k != "컬러편차"
    )
    return summary
