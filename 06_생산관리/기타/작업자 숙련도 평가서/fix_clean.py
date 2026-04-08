import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client

BASE = r'C:\Users\User\Desktop\업무리스트\06_생산관리\기타\작업자 숙련도 평가서'

excel = win32com.client.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False

FILE_MAP = {
    'SD9M01_주간 숙련도 평가서_26년 2분기.xls': ('SD9M01 주간 숙련도 평가서', '숙련도 평가서', 14),
    'SD9M01_야간 숙련도 평가서_26년 2분기.xls': ('SD9M01 야간 숙련도 평가서', '숙련도 평가서', 14),
    'SP3M3_주간 작업자 숙련도 평가서_26년 2분기.xls': ('SP3M3 주간 숙련도 평가서', '종합', 13),
    'SP3M3_야간 작업자 숙련도 평가서_26년 2분기.xls': ('SP3M3 야간 숙련도 평가서', '종합', 13),
}

total = 0

for src_file, (folder_name, skip_sheet, proc_col) in FILE_MAP.items():
    src_path = os.path.join(BASE, src_file)
    out_dir = os.path.join(BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)
    print(f'\n--- {src_file} ---')

    wb_src = excel.Workbooks.Open(src_path, UpdateLinks=0, ReadOnly=True)

    for i in range(1, wb_src.Sheets.Count + 1):
        ws_src = wb_src.Sheets(i)
        if ws_src.Name == skip_sheet:
            continue

        target_name = ws_src.Name
        out_name = target_name + ' 숙련도 평가서 (26.04.01).xlsx'
        out_path = os.path.join(out_dir, out_name)

        try:
            # 새 워크북 생성
            wb_new = excel.Workbooks.Add()
            ws_new = wb_new.Sheets(1)
            ws_new.Name = target_name

            # 원본 UsedRange 복사 -> 새 시트에 붙여넣기
            src_range = ws_src.UsedRange
            src_range.Copy()

            # 전체 붙여넣기 (서식+값)
            ws_new.Range('A1').PasteSpecial(Paste=-4104)  # xlPasteAll -> 값+서식
            excel.CutCopyMode = False

            # 열 너비 복사
            for c in range(1, src_range.Columns.Count + 1):
                ws_new.Columns(c).ColumnWidth = ws_src.Columns(c).ColumnWidth

            # 행 높이 복사
            for r in range(1, src_range.Rows.Count + 1):
                ws_new.Rows(r).RowHeight = ws_src.Rows(r).RowHeight

            # 병합 셀 복사
            for area in ws_src.UsedRange.MergeArea if hasattr(ws_src.UsedRange, 'MergeArea') else []:
                pass  # MergeArea는 개별 셀에서 확인

            # 값으로 다시 덮어쓰기 (수식 완전 제거)
            used_new = ws_new.UsedRange
            used_new.Copy()
            used_new.PasteSpecial(Paste=-4163)  # xlPasteValues
            excel.CutCopyMode = False

            # SP3M3: 공정NO=430, 공정명 설정
            if 'SP3M3' in folder_name:
                line_col = 8
                proc_no_col = 13
                proc_name_col = 18
                ws_new.Cells(5, line_col).Value = 'SPM3'
                ws_new.Cells(5, proc_no_col).Value = 430
                ws_new.Cells(5, proc_name_col).Value = '프레임 앗세이 & 최종 검사 포장'

            # SD9M01: 110->100
            if 'SD9M01' in folder_name:
                proc_no = ws_new.Cells(5, proc_col).Value
                if proc_no is not None and int(proc_no) == 110:
                    ws_new.Cells(5, proc_col).Value = 100
                    print(f'  FIX: {target_name} 110->100')

            # 기본 Sheet2, Sheet3 삭제
            while wb_new.Sheets.Count > 1:
                wb_new.Sheets(wb_new.Sheets.Count).Delete()

            wb_new.SaveAs(out_path, FileFormat=51)
            wb_new.Close(False)
            total += 1
            print(f'  OK: {out_name}')
        except Exception as e:
            print(f'  ERROR: {out_name} -> {e}')
            try:
                excel.ActiveWorkbook.Close(False)
            except:
                pass

    wb_src.Close(False)

excel.Quit()
print(f'\n완료: {total}개')
