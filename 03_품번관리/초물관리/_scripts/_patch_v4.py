# -*- coding: utf-8 -*-
"""v4 패치: 배경색 통일 + empty 시트 수정 + 병합 재확인"""
import win32com.client, os

WORK = r"C:\Users\User\Desktop\업무리스트\03_품번관리\초물관리"
os.chdir(WORK)

COLOR_BLACK = 0x000000
COLOR_RED = 0x0000FF
COLOR_DARKBLUE = 0xFF0000
BG_SKYBLUE = 0xFFCC99  # ColorIndex 37

excel = win32com.client.gencache.EnsureDispatch("Excel.Application")
excel.Visible = False; excel.DisplayAlerts = False

output_dir = os.path.abspath("_output")
files = sorted(os.listdir(output_dir))
stats = {"fixed_empty": 0, "fixed_merge": 0, "fixed_bg": 0}

for fi, fname in enumerate(files):
    fp = os.path.join(output_dir, fname)
    if not (fname.endswith(".xls") or fname.endswith(".xlsx")):
        continue
    try:
        wb = excel.Workbooks.Open(fp, UpdateLinks=0)
    except:
        continue

    changed = False
    for si in range(1, wb.Sheets.Count + 1):
        ws = wb.Sheets(si)
        sname = ws.Name
        ws.Activate()

        # === 1. 배경색 통일 ===
        try:
            ws.Range("AB1:AJ14").Interior.Color = BG_SKYBLUE
            stats["fixed_bg"] += 1
            changed = True
        except:
            pass

        # === 2. 병합 검증/수정 ===
        ab5 = ws.Range("AB5")
        ab10 = ws.Range("AB10")
        ab13 = ws.Range("AB13")

        # 정상 병합: AB5:AJ9, AB10:AJ12, AB13:AJ14
        need_fix = False
        try:
            if ab5.MergeCells:
                ma5 = ab5.MergeArea.Address
                if ma5 != "$AB$5:$AJ$9":
                    need_fix = True
            else:
                need_fix = True
            if ab10.MergeCells:
                ma10 = ab10.MergeArea.Address
                if ma10 != "$AB$10:$AJ$12":
                    need_fix = True
            else:
                need_fix = True
            if ab13.MergeCells:
                ma13 = ab13.MergeArea.Address
                if ma13 != "$AB$13:$AJ$14":
                    need_fix = True
            else:
                need_fix = True
        except:
            need_fix = True

        if need_fix:
            # 현재 값 읽기
            v5 = ab5.Value
            v10 = ab10.Value
            v13 = ab13.Value

            # H12 LH/RH
            h12_raw = str(ws.Cells(12, 8).Value or "")
            h12_first = h12_raw.split(chr(10))[0].strip().upper().replace(" ","").replace("-","")
            p = h12_first[:5]
            lhrh = "LH" if p in ("88810","89870") else "RH" if p in ("88820","89880") else None
            sc = COLOR_RED if lhrh == "LH" else COLOR_DARKBLUE if lhrh == "RH" else COLOR_RED

            # 전체 병합 해제
            for r in range(5, 15):
                for c in range(28, 37):
                    try:
                        cc = ws.Cells(r, c)
                        if cc.MergeCells:
                            cc.MergeArea.UnMerge()
                    except: pass
            ws.Range("AB5:AJ14").ClearContents()

            # empty 판별
            if v5 is None or str(v5).strip() == "" or str(v5).strip() == "SP3M3":
                if v10 is None or str(v10).strip() == "":
                    v10 = sname  # 시트명 사용
                    stats["fixed_empty"] += 1

            # 재병합
            rng1 = ws.Range("AB5:AJ9")
            rng1.Merge(); rng1.Value = "SP3M3" if (v5 is None or str(v5).strip() in ("","SP3M3","SP3S03")) else v5
            rng1.Font.Size = 85; rng1.Font.Bold = True; rng1.Font.Color = COLOR_BLACK
            rng1.Font.Name = "HY헤드라인M"
            rng1.HorizontalAlignment = -4108; rng1.VerticalAlignment = -4108
            rng1.WrapText = False; rng1.ShrinkToFit = False

            rng2 = ws.Range("AB10:AJ12")
            rng2.Merge()
            try: rng2.Value = int(v10) if v10 else v10
            except: rng2.Value = v10
            rng2.Font.Size = 110; rng2.Font.Bold = True; rng2.Font.Color = sc
            rng2.Font.Name = "HY헤드라인M"
            rng2.HorizontalAlignment = -4108; rng2.VerticalAlignment = -4108
            rng2.WrapText = False; rng2.ShrinkToFit = False

            rng3 = ws.Range("AB13:AJ14")
            rng3.Merge()
            rsp_val = str(v13 or "")
            rng3.Value = rsp_val if rsp_val else ""
            rng3.Font.Size = 80; rng3.Font.Bold = True; rng3.Font.Color = COLOR_BLACK
            rng3.Font.Name = "HY헤드라인M"
            rng3.HorizontalAlignment = -4108; rng3.VerticalAlignment = -4108
            rng3.WrapText = False; rng3.ShrinkToFit = False

            # RSP 부분색상
            if rsp_val and rsp_val.startswith("RSP") and lhrh:
                ms = 4; me = ms
                for ch in rsp_val[ms:]:
                    if ch.isdigit(): break
                    me += 1
                if me > ms:
                    try:
                        clr = COLOR_RED if lhrh == "LH" else COLOR_DARKBLUE
                        rng3.GetCharacters(ms+1, me-ms).Font.Color = clr
                    except: pass

            stats["fixed_merge"] += 1
            changed = True

        # === 3. 안쪽 구분선 제거 ===
        try:
            for idx in [11, 12]:
                ws.Range("AB5:AJ14").Borders(idx).LineStyle = -4142
        except: pass

    if changed:
        wb.Sheets(1).Activate()
        wb.Windows(1).View = 1
        wb.Save()
    wb.Close(False)

    if (fi+1) % 10 == 0:
        print(f"  {fi+1}/{len(files)}")

excel.Quit()
print(f"\nDone: bg={stats['fixed_bg']} merge={stats['fixed_merge']} empty={stats['fixed_empty']}")
