# -*- coding: utf-8 -*-
"""전체 초물표 일괄 적용 v3 - 새 분할 + C안 통일 + 안쪽 구분선 제거"""
import win32com.client, os, shutil, openpyxl

WORK = r"C:\Users\User\Desktop\업무리스트\03_품번관리\초물관리"
os.chdir(WORK)

# === 기준정보 로드 ===
ref_wb = openpyxl.load_workbook("SP3M3_모듈품번_최신.xlsx", data_only=True)
ref_ws = ref_wb.active
ref_map = {}
for r in range(2, ref_ws.max_row + 1):
    partno = str(ref_ws.cell(r, 2).value or "")
    rsp = str(ref_ws.cell(r, 4).value or "")
    norm = partno.upper().replace(" ", "").replace("-", "")
    if norm and rsp:
        ref_map[norm] = rsp
print(f"[INFO] ref: {len(ref_map)} entries")

def normalize(s):
    return str(s).upper().replace(" ", "").replace("-", "")

def parse_ab5(ws):
    val = str(ws.Cells(5, 28).Value or "")
    lines = [l.strip() for l in val.split(chr(10)) if l.strip()]
    has_rsp = len(lines) >= 3 and lines[2].startswith("RSP")
    return lines, has_rsp

def get_lhrh(h12_norm):
    p = h12_norm[:5]
    if p in ("88810", "89870"): return "LH"
    if p in ("88820", "89880"): return "RH"
    return None

COLOR_BLACK = 0x000000
COLOR_RED = 0x0000FF
COLOR_DARKBLUE = 0xFF0000

def unmerge_area(ws):
    for r in range(5, 15):
        for c in range(28, 37):
            try:
                cc = ws.Cells(r, c)
                if cc.MergeCells:
                    cc.MergeArea.UnMerge()
            except:
                pass
    ws.Range("AB5:AJ14").ClearContents()

def apply_c_plan(ws, sub_val, rsp_val, lhrh):
    unmerge_area(ws)
    rng1 = ws.Range("AB5:AJ9")
    rng1.Merge(); rng1.Value = "SP3M3"
    rng1.Font.Size = 85; rng1.Font.Bold = True; rng1.Font.Color = COLOR_BLACK
    rng1.Font.Name = "HY헤드라인M"
    rng1.HorizontalAlignment = -4108; rng1.VerticalAlignment = -4108
    rng1.WrapText = False; rng1.ShrinkToFit = False

    rng2 = ws.Range("AB10:AJ12")
    rng2.Merge()
    try: rng2.Value = int(sub_val)
    except: rng2.Value = sub_val
    sc = COLOR_RED if lhrh == "LH" else COLOR_DARKBLUE if lhrh == "RH" else COLOR_RED
    rng2.Font.Size = 110; rng2.Font.Bold = True; rng2.Font.Color = sc
    rng2.Font.Name = "HY헤드라인M"
    rng2.HorizontalAlignment = -4108; rng2.VerticalAlignment = -4108
    rng2.WrapText = False; rng2.ShrinkToFit = False

    rng3 = ws.Range("AB13:AJ14")
    rng3.Merge(); rng3.Value = rsp_val
    rng3.Font.Size = 80; rng3.Font.Bold = True; rng3.Font.Color = COLOR_BLACK
    rng3.Font.Name = "HY헤드라인M"
    rng3.HorizontalAlignment = -4108; rng3.VerticalAlignment = -4108
    rng3.WrapText = False; rng3.ShrinkToFit = False

    if rsp_val and rsp_val.startswith("RSP") and lhrh:
        ms = 4; me = ms
        for ch in rsp_val[ms:]:
            if ch.isdigit(): break
            me += 1
        if me > ms:
            try:
                clr = COLOR_RED if lhrh == "LH" else COLOR_DARKBLUE
                rng3.GetCharacters(ms + 1, me - ms).Font.Color = clr
            except: pass

    for idx in [11, 12]:
        ws.Range("AB5:AJ14").Borders(idx).LineStyle = -4142

def apply_2split(ws, sub_val, lhrh):
    unmerge_area(ws)
    rng1 = ws.Range("AB5:AJ9")
    rng1.Merge(); rng1.Value = "SP3M3"
    rng1.Font.Size = 85; rng1.Font.Bold = True; rng1.Font.Color = COLOR_BLACK
    rng1.Font.Name = "HY헤드라인M"
    rng1.HorizontalAlignment = -4108; rng1.VerticalAlignment = -4108
    rng1.WrapText = False; rng1.ShrinkToFit = False

    rng2 = ws.Range("AB10:AJ14")
    rng2.Merge()
    try: rng2.Value = int(sub_val)
    except: rng2.Value = sub_val
    sc = COLOR_RED if lhrh == "LH" else COLOR_DARKBLUE if lhrh == "RH" else COLOR_RED
    rng2.Font.Size = 110; rng2.Font.Bold = True; rng2.Font.Color = sc
    rng2.Font.Name = "HY헤드라인M"
    rng2.HorizontalAlignment = -4108; rng2.VerticalAlignment = -4108
    rng2.WrapText = False; rng2.ShrinkToFit = False

    for idx in [11, 12]:
        ws.Range("AB5:AJ14").Borders(idx).LineStyle = -4142

# === 메인 ===
backup_dir = os.path.abspath("_backup")
output_dir = os.path.abspath("_output")
os.makedirs(output_dir, exist_ok=True)

files = sorted(os.listdir(backup_dir))
print(f"[INFO] {len(files)} files")

excel = win32com.client.gencache.EnsureDispatch("Excel.Application")
excel.Visible = False; excel.DisplayAlerts = False

stats = {"input": 0, "modify": 0, "keep": 0, "nomatch": 0, "sheets": 0, "fail_files": 0}
log = []

for fi, fname in enumerate(files):
    src = os.path.join(backup_dir, fname)
    dst = os.path.join(output_dir, fname)
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copy2(src, dst)

    try:
        wb = excel.Workbooks.Open(dst, UpdateLinks=0)
    except Exception as e:
        log.append(f"[FAIL] {fname}: {str(e)[:40]}")
        stats["fail_files"] += 1
        continue

    flog = []
    for si in range(1, wb.Sheets.Count + 1):
        ws = wb.Sheets(si)
        sname = ws.Name
        stats["sheets"] += 1
        ws.Activate()

        wb.Windows(1).View = 1
        ws.DisplayPageBreaks = False
        try: ws.ResetAllPageBreaks()
        except: pass

        try:
            used = ws.UsedRange
            lr = used.Row + used.Rows.Count - 1
            lcc = min(used.Column + used.Columns.Count - 1, 36)
            full = ws.Range(ws.Cells(1, 2), ws.Cells(lr, lcc))
            for idx in [11, 12]:
                b = full.Borders(idx); b.LineStyle = 1; b.Weight = 2; b.Color = 0
            for idx in [7, 8, 9, 10]:
                b = full.Borders(idx); b.LineStyle = 1; b.Weight = -4138; b.Color = 0
        except: pass

        h12_raw = str(ws.Cells(12, 8).Value or "")
        h12_first = h12_raw.split(chr(10))[0].strip()
        h12_norm = normalize(h12_first)
        lhrh = get_lhrh(h12_norm)
        lines, has_rsp = parse_ab5(ws)
        esub = lines[1] if len(lines) >= 2 else ""
        ersp = lines[2] if has_rsp else ""

        if h12_norm in ref_map:
            rr = ref_map[h12_norm]
            if not has_rsp:
                apply_c_plan(ws, esub, rr, lhrh)
                flog.append(f"  {sname}: INPUT->{rr}")
                stats["input"] += 1
            elif ersp != rr:
                apply_c_plan(ws, esub, rr, lhrh)
                flog.append(f"  {sname}: MOD {ersp}->{rr}")
                stats["modify"] += 1
            else:
                apply_c_plan(ws, esub, ersp, lhrh)
                flog.append(f"  {sname}: KEEP")
                stats["keep"] += 1
        else:
            if ersp:
                apply_c_plan(ws, esub, ersp, lhrh)
                flog.append(f"  {sname}: NOMATCH rsp={ersp}")
            elif esub:
                apply_2split(ws, esub, lhrh)
                flog.append(f"  {sname}: NOMATCH 2split")
            else:
                flog.append(f"  {sname}: NOMATCH empty")
            stats["nomatch"] += 1

    wb.Sheets(1).Activate()
    wb.Windows(1).View = 1
    try:
        wb.Save(); wb.Close(False)
        log.append(f"[OK] {fname}")
        log.extend(flog)
    except Exception as e:
        log.append(f"[FAIL] {fname}: save {str(e)[:40]}")
        stats["fail_files"] += 1
        try: wb.Close(False)
        except: pass

    if (fi + 1) % 10 == 0:
        print(f"  {fi+1}/{len(files)}")

excel.Quit()

print(f"\n{'='*50}")
print(f"files={len(files)} sheets={stats['sheets']}")
print(f"INPUT={stats['input']} MOD={stats['modify']} KEEP={stats['keep']} NOMATCH={stats['nomatch']} FAIL={stats['fail_files']}")
print(f"{'='*50}")
for r in log:
    print(r)
