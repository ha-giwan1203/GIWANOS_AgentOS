"""
마스터(V2)에 SP3M3·HCAMS02 라인 누락 행 신규 등록 + 오류리스트 양식 재작성.

핵심 룰:
- 조립품번은 신규 시퀀스 자동 부여 (마스터 max + 1부터, 충돌 회피)
- 충돌 set: V2 마스터 SP3M3/HCAMS02 시트 기존 + ERP cache PART_NO 합집합
- 같은 모품번 등록 컬러의 조립품번 직접 재사용 금지 (ERP unique 제약)
- 마스터 신규 행 등록 후 → 오류리스트 양식에 신규 시퀀스로 작성

흐름:
1. V2 마스터 백업 (_pre_assyreg_YYYYMMDD_HHMMSS)
2. 충돌 set 구성 (마스터 + ERP cache PART_NO)
3. 43행 신규 시퀀스 부여
4. 마스터 SP3M3/HCAMS02 시트에 append
5. 마스터 save
6. 오류리스트 양식 재작성
"""
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


REPO = Path(r"C:\Users\User\Desktop\업무리스트")
MASTER = REPO / "05_생산실적/조립비정산/01_기준정보/기준정보_라인별정리_최종_V2_20260506.xlsx"
CACHE = REPO / "05_생산실적/조립비정산/05월/_cache/erp_lookup_SP3M3_20260509.json"
CHECK = REPO / "05_생산실적/조립비정산/05월/등록누락점검_SP3M3_20260509/등록누락점검_SP3M3_20260509.xlsx"
ERR_XLSX = Path(r"\\210.216.217.180\zz-group\★ 신규 시스템\1. GERP 조립비\완료\정합성 검증\★ 2026년 오류리스트\4월 오류리스트\대원테크\오류리스트_04월_추가.xlsx")

PRIMARY = "SP3M3"
PAIRED = "HCAMS02"
TARGET_CMPY = "0109"


def collect_part_nos(ws, col_part=4):
    s = set()
    for row in ws.iter_rows(min_row=4, values_only=True):
        if len(row) >= col_part and row[col_part - 1]:
            s.add(str(row[col_part - 1]).strip())
    return s


def collect_erp_part_nos(cache, line):
    s = set()
    for pn, entry in cache.items():
        for color, rows in entry.get("lines_by_color", {}).items():
            for r in rows:
                if r.get("ASSY_LINE_CD") == line:
                    part = r.get("PART_NO")
                    if part:
                        s.add(str(part).strip())
    return s


def parse_max_seq(part_set, line):
    """SP3M{N} 또는 HCAMS02-{N} 또는 HCAMS02_{NN}_{NN}_{NNNN} 등 시퀀스 max 추출."""
    pats = []
    if line == "SP3M3":
        pats = [re.compile(r"^SP3M(\d+)$")]
    elif line == "HCAMS02":
        pats = [
            re.compile(r"^HCAMS02-(\d+)$"),
            re.compile(r"^HCAMS02_(\d+)$"),
        ]
    maxv = 0
    for x in part_set:
        for p in pats:
            m = p.match(x)
            if m:
                v = int(m.group(1))
                if v > maxv:
                    maxv = v
                break
    return maxv


def gen_new_part(used_set, line, current_n):
    """현재 N부터 시작해 충돌 안 나는 첫 번호 반환."""
    n = current_n
    while True:
        if line == "SP3M3":
            cand = f"SP3M{n}"
        else:  # HCAMS02
            cand = f"HCAMS02-{n:05d}"
        if cand not in used_set:
            return cand, n
        n += 1


def load_classified_rows():
    """등록누락점검 xlsx의 라인누락 4시트 + 컬러편차 시트 → 43행 build_rows 재실행."""
    sys.path.insert(0, str(Path(__file__).parent))
    import fill_error_list as fel
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    classified = fel.load_classify()
    rows = fel.build_rows(cache, classified)
    return rows, cache


def main():
    # 1. 백업
    bak = MASTER.with_name(MASTER.stem + f"_pre_assyreg_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
    shutil.copy(MASTER, bak)
    print(f"[1/6] 마스터 백업: {bak.name}")

    # 2. 마스터 load + 충돌 set 구성
    wb = openpyxl.load_workbook(MASTER)
    sp_ws = wb["SP3M3"]
    hc_ws = wb["HCAMS02"]
    sp_master = collect_part_nos(sp_ws)
    hc_master = collect_part_nos(hc_ws)
    print(f"[2/6] 마스터 SP3M3 조립품번 {len(sp_master)} / HCAMS02 {len(hc_master)}")

    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    sp_erp = collect_erp_part_nos(cache, "SP3M3")
    hc_erp = collect_erp_part_nos(cache, "HCAMS02")
    print(f"  ERP cache SP3M3 PART_NO {len(sp_erp)} / HCAMS02 {len(hc_erp)}")

    sp_used = sp_master | sp_erp
    hc_used = hc_master | hc_erp
    sp_max = parse_max_seq(sp_used, "SP3M3")
    hc_max = parse_max_seq(hc_used, "HCAMS02")
    print(f"  사용중 max SP3M3={sp_max} / HCAMS02={hc_max}")

    # 3. 43행 신규 시퀀스 부여
    rows, _ = load_classified_rows()
    print(f"[3/6] 분류 행: {len(rows)}건")

    sp_next = sp_max + 1
    hc_next = hc_max + 1
    new_master_rows = {"SP3M3": [], "HCAMS02": []}

    for r in rows:
        line = r["라인코드"]
        if line == "SP3M3":
            new_part, sp_next = gen_new_part(sp_used, "SP3M3", sp_next)
            sp_used.add(new_part)
            sp_next += 1
        else:
            new_part, hc_next = gen_new_part(hc_used, "HCAMS02", hc_next)
            hc_used.add(new_part)
            hc_next += 1
        r["조립품번"] = new_part
        # 마스터 행 (8컬럼)
        new_master_rows[line].append([
            r["품번"], TARGET_CMPY, line, new_part,
            r.get("Usage", 1), r.get("단가구분") or "정단가",
            r.get("단가"), r["차종"],
        ])

    print(f"  신규 시퀀스: SP3M3 {sp_max+1}~{sp_next-1} ({len(new_master_rows['SP3M3'])}개)")
    print(f"               HCAMS02 {hc_max+1}~{hc_next-1} ({len(new_master_rows['HCAMS02'])}개)")

    # 4. 마스터 시트에 append
    for nr in new_master_rows["SP3M3"]:
        sp_ws.append(nr)
    for nr in new_master_rows["HCAMS02"]:
        hc_ws.append(nr)
    print(f"[4/6] 마스터 append: SP3M3 +{len(new_master_rows['SP3M3'])} / HCAMS02 +{len(new_master_rows['HCAMS02'])}")

    # 5. 마스터 save
    wb.save(MASTER)
    print(f"[5/6] 마스터 save: {MASTER.name}")

    # 5.5 신규 시퀀스 결과 JSON 보존 (양식 저장 실패 시 후속 재작성용)
    rows_json = REPO / "05_생산실적/조립비정산/05월/_cache/registered_rows.json"
    rows_json.parent.mkdir(parents=True, exist_ok=True)
    rows_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"  신규 시퀀스 결과 JSON: {rows_json}")

    # 6. 오류리스트 양식 재작성 (실패해도 마스터·JSON은 보존)
    sys.path.insert(0, str(Path(__file__).parent))
    import fill_error_list as fel
    try:
        fel.write_to_err_xlsx(rows)
        print(f"[6/6] 오류리스트 양식 재작성: {ERR_XLSX.name}")
    except PermissionError:
        print(f"[6/6] 오류리스트 양식 저장 실패 — 파일이 열려있음")
        print(f"  사용자가 '{ERR_XLSX.name}' 닫은 후 `python apply_to_err_xlsx.py` 재실행")

    print(f"\n=== 완료 ===")
    print(f"마스터: SP3M3 +{len(new_master_rows['SP3M3'])}행 / HCAMS02 +{len(new_master_rows['HCAMS02'])}행")
    print(f"오류리스트: {len(rows)}행 (신규 시퀀스로)")


if __name__ == "__main__":
    main()
