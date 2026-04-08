"""
숙련도 평가서 양식 통일 — SP3M3
- SD9M01 곽은란 양식(템플릿)을 SP3M3에도 동일 사용
- 라인명만 SP3M3으로 변경, 공정번호/공정명은 MES 기준
- 비율/합계/등급 수식 보존 (값 덮어쓰기 금지)
- XML 정리 (externalLinks, definedNames 제거)
"""
import sys, os, re, zipfile
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client

BASE = r'C:\Users\User\Desktop\업무리스트\06_생산관리\기타\작업자 숙련도 평가서'

# MES 기준 공정 배정 (API: /wrk/selectListWrkProcIByWrk.do)
PROC_NAMES = {
    10: 'RETRACTOR MAIN FRAME 앗세이 로딩 & 스풀 로딩 & 바코드 부착',
    11: 'WEBBING GUIDE 앗세이 조립',
    91: 'LOCKING 토션 조립 & LOCKING 베이스 락 조립',
    140: 'RETRACTOR COMMON 볼 가이드 조립 & 파이프 조립 & 플레이트 커버 조립',
    340: 'VEHICLE SENSOR & 센서 커버 & 센스 브라켓 조립',
    430: 'RETRACTOR MAIN FRAME 앗세이 & 최종 검사 포장',
}

MES_SP3 = {
    '박지영': {'main': (91, PROC_NAMES[91]), 'sub': [(140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340]), (11, PROC_NAMES[11])]},
    '김아름': {'main': (430, PROC_NAMES[430]), 'sub': []},
    '정미량': {'main': (340, PROC_NAMES[340]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (11, PROC_NAMES[11])]},
    '김경순': {'main': (140, PROC_NAMES[140]), 'sub': [(91, PROC_NAMES[91]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340]), (11, PROC_NAMES[11])]},
    '이민주': {'main': (11, PROC_NAMES[11]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340])]},
    '최인선': {'main': (10, PROC_NAMES[10]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (340, PROC_NAMES[340]), (11, PROC_NAMES[11])]},
    '박경혜': {'main': (11, PROC_NAMES[11]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340])]},
    '도티수안': {'main': (140, PROC_NAMES[140]), 'sub': [(91, PROC_NAMES[91]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340]), (11, PROC_NAMES[11])]},
    '김미령': {'main': (430, PROC_NAMES[430]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340]), (11, PROC_NAMES[11])]},
    '이선미': {'main': (91, PROC_NAMES[91]), 'sub': [(140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340]), (11, PROC_NAMES[11])]},
    '제인옥': {'main': (11, PROC_NAMES[11]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (340, PROC_NAMES[340])]},
    '김하이': {'main': (340, PROC_NAMES[340]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (10, PROC_NAMES[10]), (11, PROC_NAMES[11])]},
    '티란': {'main': (10, PROC_NAMES[10]), 'sub': [(91, PROC_NAMES[91]), (140, PROC_NAMES[140]), (340, PROC_NAMES[340]), (11, PROC_NAMES[11])]},
}

SECTION_WIDTH = 32  # SD9M01 곽은란 양식 기준 섹션 폭
COLOR_MAIN = 15773696   # 주공정 담당 셀 배경색 (파란)
COLOR_SUB = 16777164    # 전환공정 담당 셀 배경색 (연노란)
SCORE_ROWS = list(range(9, 28))
SCORE_COL = 29

# SD9M01 곽은란 양식을 템플릿으로 사용
TEMPLATE_FILE = 'SD9M01_주간 숙련도 평가서_26년 2분기.xls'
TEMPLATE_SHEET = '곽은란'

# SP3M3 원본 파일 (데이터 읽기용)
SP3_FILES = {
    'SP3M3_주간 작업자 숙련도 평가서_26년 2분기.xls': ('SP3M3 주간 숙련도 평가서', '종합'),
    'SP3M3_야간 작업자 숙련도 평가서_26년 2분기.xls': ('SP3M3 야간 숙련도 평가서', '종합'),
}


def detect_offset(ws):
    for c in [1, 2]:
        v = ws.Cells(2, c).Value
        if v and '숙련도' in str(v):
            return c - 2
    return 0


def read_main_data(ws, off):
    d = {}
    d['name'] = ws.Cells(2, 22 + off).Value
    d['empNo'] = ws.Cells(3, 22 + off).Value
    d['line'] = ws.Cells(5, 9 + off).Value
    d['procNo'] = ws.Cells(5, 14 + off).Value
    d['procNm'] = ws.Cells(5, 19 + off).Value
    d['date'] = ws.Cells(5, 28 + off).Value
    d['scores'] = [ws.Cells(r, 29 + off).Value for r in SCORE_ROWS]
    return d


def clean_xml(fpath):
    tmp = fpath + '.tmp'
    try:
        with zipfile.ZipFile(fpath, 'r') as zin:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if 'externalLinks' in item.filename:
                        continue
                    data = zin.read(item.filename)
                    if item.filename == '[Content_Types].xml':
                        data = re.sub(rb'<Override[^>]*externalLink[^>]*/>', b'', data)
                    if item.filename == 'xl/_rels/workbook.xml.rels':
                        data = re.sub(rb'<Relationship[^>]*externalLink[^>]*/>', b'', data)
                    if item.filename == 'xl/workbook.xml':
                        data = re.sub(rb'<definedNames>.*?</definedNames>', b'', data, flags=re.DOTALL)
                    zout.writestr(item, data)
        os.replace(tmp, fpath)
        return True
    except Exception as e:
        print(f'  XML FAIL: {os.path.basename(fpath)} -> {e}')
        try:
            os.remove(tmp)
        except:
            pass
        return False


excel = win32com.client.Dispatch('Excel.Application')
excel.Visible = False
excel.DisplayAlerts = False

# ====== 1단계: SP3M3 원본에서 데이터 읽기 ======
print('--- 1단계: SP3M3 원본 데이터 읽기 ---')
all_workers = []

for src_file, (folder_name, skip_sheet) in SP3_FILES.items():
    src_path = os.path.join(BASE, src_file)
    wb_src = excel.Workbooks.Open(src_path, UpdateLinks=0, ReadOnly=True)

    for si in range(1, wb_src.Sheets.Count + 1):
        ws_src = wb_src.Sheets(si)
        name = ws_src.Name
        if name == skip_sheet:
            continue

        off = detect_offset(ws_src)
        main = read_main_data(ws_src, off)
        all_workers.append((name, folder_name, main))
        mes = MES_SP3.get(name)
        sub_count = len(mes['sub']) if mes else 0
        print(f'  {folder_name}/{name}: off={off}, MES 전환={sub_count}개')

    wb_src.Close(False)

print(f'  총 {len(all_workers)}명 읽기 완료')

# ====== 2단계: SD9M01 곽은란 양식으로 파일 생성 ======
print('\n--- 2단계: SD9M01 곽은란 양식 기반 파일 생성 ---')
tmpl_path = os.path.join(BASE, TEMPLATE_FILE)
wb_tmpl = excel.Workbooks.Open(tmpl_path, UpdateLinks=0, ReadOnly=True)
ws_gwak = wb_tmpl.Sheets(TEMPLATE_SHEET)

created_files = []

for name, folder_name, main in all_workers:
    out_dir = os.path.join(BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{name} 숙련도 평가서 (26.04.01).xlsx')

    # 곽은란 시트 복사 → 새 워크북 (서식·병합·수식 100% 보존)
    ws_gwak.Copy()
    wb_new = excel.ActiveWorkbook
    ws = wb_new.Sheets(1)

    # 외부링크 끊기
    try:
        links = wb_new.LinkSources(1)
        if links:
            for lnk in links:
                wb_new.BreakLink(lnk, 1)
    except:
        pass

    ws.Name = name

    # 기존 전환공정 영역 삭제 (col 33 이후)
    rng_clear = ws.Range(ws.Cells(1, 33), ws.Cells(50, 350))
    rng_clear.UnMerge()
    rng_clear.Clear()

    mes = MES_SP3.get(name)

    # --- 주공정 데이터 채우기 ---
    ws.Cells(2, 22).Value = main['name']
    ws.Cells(3, 22).Value = main['empNo']
    ws.Cells(3, 26).Value = '주공정'
    ws.Cells(5, 9).Value = 'SP3M3'  # 라인명 변경!

    if mes:
        ws.Cells(5, 14).Value = mes['main'][0]
        ws.Cells(5, 19).Value = mes['main'][1]
    else:
        ws.Cells(5, 14).Value = main['procNo']
        ws.Cells(5, 19).Value = main['procNm']

    ws.Cells(5, 28).Value = main['date']

    # 점수만 입력 (수식 보존)
    for i, r in enumerate(SCORE_ROWS):
        ws.Cells(r, SCORE_COL).Value = main['scores'][i]
    # 비율(R30), 합계(J32), 등급(T32)은 곽은란 수식이 자동 계산 — 값 덮어쓰기 금지

    # --- 전환공정 N개 처리 ---
    sub_list = mes['sub'] if mes else []
    if sub_list:
        for si_idx, (sub_no, sub_nm) in enumerate(sub_list):
            # 주공정 영역(col 1~32) 복사
            main_rng = ws.Range(ws.Cells(1, 1), ws.Cells(40, 32))
            main_rng.Copy()

            dest_col = 33 + (si_idx * SECTION_WIDTH)
            ws.Cells(1, dest_col).Select()
            ws.Paste()
            excel.CutCopyMode = False

            # 열 너비 맞추기
            for ci in range(1, 33):
                ws.Columns(dest_col - 1 + ci).ColumnWidth = ws.Columns(ci).ColumnWidth

            # 섹션 간 구분 열 너비 = 3
            ws.Columns(dest_col).ColumnWidth = 3

            # 전환공정 정보 교체
            off_s = dest_col - 1
            ws.Cells(3, 26 + off_s).Value = '전환공정'
            ws.Cells(5, 14 + off_s).Value = sub_no
            ws.Cells(5, 19 + off_s).Value = sub_nm

            # 담당 셀 배경색 → 전환공정(연노란)
            for dc in range(26, 32):
                ws.Cells(3, dc + off_s).Interior.Color = COLOR_SUB

    # 평가일 테두리 (모든 섹션)
    total_sections = 1 + len(sub_list)
    for sec in range(total_sections):
        sec_off = sec * SECTION_WIDTH
        date_rng = ws.Range(ws.Cells(5, 28 + sec_off), ws.Cells(5, 32 + sec_off))
        for edge in [7, 8, 9, 10]:
            date_rng.Borders(edge).LineStyle = 1
            date_rng.Borders(edge).Weight = 2

    # 이름 정리
    for n in range(wb_new.Names.Count, 0, -1):
        try:
            wb_new.Names(n).Delete()
        except:
            pass

    wb_new.SaveAs(out_path, FileFormat=51)
    wb_new.Close(False)
    created_files.append(out_path)
    print(f'  {name} -> OK (전환 {len(sub_list)}개)')

wb_tmpl.Close(False)
excel.Quit()
print(f'\n파일 생성: {len(created_files)}개')

# ====== 3단계: XML 정리 ======
print('\n--- 3단계: XML 정리 ---')
ok = 0
for fpath in created_files:
    if clean_xml(fpath):
        ok += 1
print(f'XML 정리: {ok}/{len(created_files)}개')

# ====== 검증 요약 ======
print('\n--- 검증 요약 ---')
for name, folder_name, main in all_workers:
    mes = MES_SP3.get(name)
    sub_count = len(mes['sub']) if mes else 0
    main_no = mes['main'][0] if mes else '?'
    print(f'  {name}({folder_name[:5]}): 주={main_no} 전환={sub_count}개 총={1+sub_count}섹션')

print(f'\n완료: {len(created_files)}개')
