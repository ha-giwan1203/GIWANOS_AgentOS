"""
숙련도 평가서 양식 통일 v5
- MES 기준 주공정 + 전환공정 N개 지원
- 곽은란 시트 ws.Copy()로 서식·병합 100% 보존
- XML 정리 (externalLinks, definedNames 제거)
"""
import sys, os, re, zipfile
sys.stdout.reconfigure(encoding='utf-8')
import win32com.client

BASE = r'C:\Users\User\Desktop\업무리스트\06_생산관리\기타\작업자 숙련도 평가서'

# MES 기준 공정 배정 (주공정 1개 + 전환공정 N개)
# 형식: '이름': {'main': (공정번호, 공정명), 'sub': [(공정번호, 공정명), ...]}
MES_SD9 = {
    '김순애': {
        'main': (10, 'PACKAGE 바코드 부착'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
                (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
                (40, '틸트락 작동 검사')]
    },
    '곽은란': {
        'main': (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (10, 'PACKAGE 바코드 부착'),
                (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
                (40, '틸트락 작동 검사')]
    },
    '곽명옥': {
        'main': (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (10, 'PACKAGE 바코드 부착'),
                (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
                (40, '틸트락 작동 검사')]
    },
    '노승자': {
        'main': (40, '틸트락 작동 검사'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (10, 'PACKAGE 바코드 부착'),
                (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
                (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩')]
    },
    '박태순': {
        'main': (21, 'RETRACTOR MAIN FRAME 서브 앗세이 압입 & 리벳 & 릴 하단 브라켓'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (10, 'PACKAGE 바코드 부착'),
                (100, 'PACKAGE 부품식별표 포장'),
                (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
                (80, 'TONGUE STOPPER 텅 스토퍼 조립'),
                (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (70, 'WEBBING 실 미싱'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
                (40, '틸트락 작동 검사')]
    },
    '최경림': {
        'main': (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (10, 'PACKAGE 바코드 부착'),
                (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
                (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (40, '틸트락 작동 검사')]
    },
    '정말숙': {
        'main': (70, 'WEBBING 실 미싱'),
        'sub': [(80, 'TONGUE STOPPER 텅 스토퍼 조립')]
    },
    '유수영': {
        'main': (80, 'TONGUE STOPPER 텅 스토퍼 조립'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (100, 'PACKAGE 부품식별표 포장'),
                (70, 'WEBBING 실 미싱')]
    },
    '김두이': {
        'main': (60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
        'sub': [(100, 'PACKAGE 부품식별표 포장'),
                (80, 'TONGUE STOPPER 텅 스토퍼 조립')]
    },
    '이명련': {
        'main': (100, 'PACKAGE 부품식별표 포장'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (80, 'TONGUE STOPPER 텅 스토퍼 조립')]
    },
    '조현미': {
        'main': (90, '최종 검사'),
        'sub': [(100, 'PACKAGE 부품식별표 포장')]
    },
    '구정옥': {
        'main': (80, 'TONGUE STOPPER 텅 스토퍼 조립'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (100, 'PACKAGE 부품식별표 포장')]
    },
    '뉴이': {
        'main': (10, 'PACKAGE 바코드 부착'),
        'sub': [(20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
                (40, '틸트락 작동 검사')]
    },
    '박인희': {
        'main': (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
        'sub': [(10, 'PACKAGE 바코드 부착'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
                (40, '틸트락 작동 검사')]
    },
    '빅냔': {
        'main': (30, 'WEBBING 웨빙 서브 앗세이 로딩'),
        'sub': [(10, 'PACKAGE 바코드 부착'),
                (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
                (40, '틸트락 작동 검사')]
    },
    '니니': {
        'main': (40, '틸트락 작동 검사'),
        'sub': [(10, 'PACKAGE 바코드 부착'),
                (20, 'RETRACTOR MAIN FRAME 릴 상단 브라켓 압입 & WEBBING GUIDE'),
                (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (30, 'WEBBING 웨빙 서브 앗세이 로딩')]
    },
    '티홍': {
        'main': (50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (40, '틸트락 작동 검사')]
    },
    '홍반': {
        'main': (60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
        'sub': [(50, 'TONGUE 레이저 마킹 조립 & D-RING 서브 앗세이'),
                (40, '틸트락 작동 검사')]
    },
    '튀린': {
        'main': (70, 'WEBBING 실 미싱'),
        'sub': [(80, 'TONGUE STOPPER 텅 스토퍼 조립')]
    },
    '미레': {
        'main': (80, 'TONGUE STOPPER 텅 스토퍼 조립'),
        'sub': [(70, 'WEBBING 실 미싱')]
    },
    '리': {
        'main': (90, '최종 검사'),
        'sub': []
    },
    '투이': {
        'main': (100, 'PACKAGE 부품식별표 포장'),
        'sub': [(80, 'TONGUE STOPPER 텅 스토퍼 조립')]
    },
    '안나': {
        'main': (100, 'PACKAGE 부품식별표 포장'),
        'sub': [(60, 'ANCHOR 서브 앗세이 조립 & ANCHOR 앵커 커버'),
                (80, 'TONGUE STOPPER 텅 스토퍼 조립')]
    },
    '정은정': {
        'main': (10, '웨빙 & WEBBING 서브 앗세이'),
        'sub': []
    },
}

SECTION_WIDTH = 32  # 한 공정 영역 = 32컬럼 (B~AG = col2~col33, 실제 데이터 col2~col32)
COLOR_MAIN = 15773696   # 주공정 담당 셀 배경색 (파란)
COLOR_SUB = 16777164    # 전환공정 담당 셀 배경색 (연노란)
SCORE_ROWS = list(range(9, 28))
SCORE_COL = 29
PCT_COLS = [18, 20, 22, 24, 26, 28, 30]
PCT_ROW = 30


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
    d['pct'] = [ws.Cells(PCT_ROW, c + off).Value for c in PCT_COLS]
    d['total'] = ws.Cells(32, 10 + off).Value
    d['level'] = ws.Cells(32, 20 + off).Value
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

FILE_MAP = {
    'SD9M01_주간 숙련도 평가서_26년 2분기.xls': ('SD9M01 주간 숙련도 평가서', '숙련도 평가서'),
    'SD9M01_야간 숙련도 평가서_26년 2분기.xls': ('SD9M01 야간 숙련도 평가서', '숙련도 평가서'),
}

# ====== 1단계: 모든 데이터를 메모리로 읽기 ======
print('--- 1단계: 데이터 읽기 ---')
all_workers = []  # (name, folder_name, main_data)

for src_file, (folder_name, skip_sheet) in FILE_MAP.items():
    src_path = os.path.join(BASE, src_file)
    wb_src = excel.Workbooks.Open(src_path, UpdateLinks=0, ReadOnly=True)

    for si in range(1, wb_src.Sheets.Count + 1):
        ws_src = wb_src.Sheets(si)
        if ws_src.Name == skip_sheet:
            continue

        name = ws_src.Name
        off = detect_offset(ws_src)
        main = read_main_data(ws_src, off)

        all_workers.append((name, folder_name, main))
        mes = MES_SD9.get(name)
        sub_count = len(mes['sub']) if mes else 0
        print(f'  {folder_name}/{name}: off={off}, MES 전환={sub_count}개')

    wb_src.Close(False)

# 원본 .xls에 없는 작업자 추가 — 조현미 데이터 활용 + 사번/이름 교체
johyunmi = next((w[2] for w in all_workers if w[0] == '조현미'), None)
EXTRA_WORKERS = [
    ('구정옥', 'A20241203004', 'SD9M01 주간 숙련도 평가서'),
    ('정은정', 'A20260323001', 'SD9M01 주간 숙련도 평가서'),
]
for ex_name, ex_empNo, ex_folder in EXTRA_WORKERS:
    if not any(w[0] == ex_name for w in all_workers) and johyunmi:
        ex_data = dict(johyunmi)
        ex_data['name'] = ex_name
        ex_data['empNo'] = ex_empNo
        all_workers.append((ex_name, ex_folder, ex_data))
        print(f'  {ex_name}: 원본 없음, 조현미 데이터 활용 (사번 {ex_empNo})')

print(f'  총 {len(all_workers)}명 읽기 완료')

# ====== 2단계: 곽은란 시트에서 ws.Copy()로 파일 생성 ======
print('\n--- 2단계: 파일 생성 ---')
tmpl_src = os.path.join(BASE, 'SD9M01_주간 숙련도 평가서_26년 2분기.xls')
wb_tmpl = excel.Workbooks.Open(tmpl_src, UpdateLinks=0, ReadOnly=True)
ws_gwak = wb_tmpl.Sheets('곽은란')

created_files = []

for name, folder_name, main in all_workers:
    out_dir = os.path.join(BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{name} 숙련도 평가서 (26.04.01).xlsx')

    # 곽은란 시트 복사 → 새 워크북 (서식·병합 100% 보존)
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

    # 시트명 변경
    ws.Name = name

    # 기존 전환공정 영역 삭제 (C33 이후)
    rng_clear = ws.Range(ws.Cells(1, 33), ws.Cells(50, 120))
    rng_clear.UnMerge()
    rng_clear.Clear()

    # MES 데이터 가져오기
    mes = MES_SD9.get(name)

    # --- 주공정 데이터 채우기 ---
    ws.Cells(2, 22).Value = main['name']
    ws.Cells(3, 22).Value = main['empNo']
    ws.Cells(3, 26).Value = '주공정'
    ws.Cells(5, 9).Value = main['line']

    if mes:
        ws.Cells(5, 14).Value = mes['main'][0]
        ws.Cells(5, 19).Value = mes['main'][1]
    else:
        ws.Cells(5, 14).Value = main['procNo']
        ws.Cells(5, 19).Value = main['procNm']

    ws.Cells(5, 28).Value = main['date']

    for i, r in enumerate(SCORE_ROWS):
        ws.Cells(r, SCORE_COL).Value = main['scores'][i]
    # 비율(R30), 합계(J32), 등급(T32)은 곽은란 원본 수식이 자동 계산 — 값 덮어쓰기 금지

    # --- 전환공정 N개 처리 ---
    sub_list = mes['sub'] if mes else []
    if sub_list:
        for si_idx, (sub_no, sub_nm) in enumerate(sub_list):
            # 채워진 주공정(C1~C32, R1~R40) 복사 — col32 포함 (평가일 병합 끝)
            main_rng = ws.Range(ws.Cells(1, 1), ws.Cells(40, 32))
            main_rng.Copy()

            # 붙여넣기 위치: C33 + (si_idx * 32)
            dest_col = 33 + (si_idx * SECTION_WIDTH)
            ws.Cells(1, dest_col).Select()
            ws.Paste()
            excel.CutCopyMode = False

            # 열 너비 맞추기 (32컬럼)
            for ci in range(1, 33):
                ws.Columns(dest_col - 1 + ci).ColumnWidth = ws.Columns(ci).ColumnWidth

            # 섹션 간 구분 열(복사된 col1 위치) 너비 = 3
            ws.Columns(dest_col).ColumnWidth = 3

            # 전환공정 정보만 교체
            off_s = dest_col - 1  # col 1 → dest_col이므로 offset = dest_col - 1
            ws.Cells(3, 26 + off_s).Value = '전환공정'
            ws.Cells(5, 14 + off_s).Value = sub_no
            ws.Cells(5, 19 + off_s).Value = sub_nm

            # 담당 셀 배경색 변경: 주공정(파란) → 전환공정(연노란)
            for dc in range(26, 32):  # C26~C31 (6셀)
                ws.Cells(3, dc + off_s).Interior.Color = COLOR_SUB

    # 평가일 테두리 추가 (모든 섹션: 주공정 + 전환공정)
    total_sections = 1 + len(sub_list)
    for sec in range(total_sections):
        sec_off = sec * SECTION_WIDTH
        # 평가일 병합셀 = (5, 28+off) ~ (5, 32+off), 상하좌우 테두리
        date_rng = ws.Range(ws.Cells(5, 28 + sec_off), ws.Cells(5, 32 + sec_off))
        for edge in [7, 8, 9, 10]:  # Left, Top, Bottom, Right
            date_rng.Borders(edge).LineStyle = 1  # xlContinuous
            date_rng.Borders(edge).Weight = 2     # xlThin

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
    mes = MES_SD9.get(name)
    sub_count = len(mes['sub']) if mes else 0
    total_sections = 1 + sub_count
    print(f'  {name}({folder_name[:5]}): 주={mes["main"][0] if mes else "?"} 전환={sub_count}개 총={total_sections}섹션')

print(f'\n완료: {len(created_files)}개')
