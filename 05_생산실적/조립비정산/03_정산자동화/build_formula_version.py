"""수식 기반 정산 파일 생성 스크립트"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("=== 수식 기반 정산 파일 생성 ===")

# Styles
header_font = Font(bold=True, size=11)
header_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
gerp_fill = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
olderp_fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
summary_fill = PatternFill(start_color='FCE4D6', end_color='FCE4D6', fill_type='solid')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
num_fmt = '#,##0;-#,##0;"-"'

# 1. Load sources
print("1. 기준정보 로딩...")
ref_wb = openpyxl.load_workbook(
    os.path.join(BASE, '01_기준정보', '기준정보_라인별정리_최종_V1_20260316.xlsx'),
    data_only=True)

print("2. GERP 실적 로딩...")
gerp_wb = openpyxl.load_workbook(
    os.path.join(BASE, '04월', '실적데이터', 'G-ERP 3월실적.xlsx'),
    data_only=True)
gerp_ws = gerp_wb[gerp_wb.sheetnames[0]]

print("3. 구ERP 실적 로딩...")
olderp_wb = openpyxl.load_workbook(
    os.path.join(BASE, '04월', '실적데이터', '구ERP 3월 실적.xlsx'),
    data_only=True)
olderp_ws = olderp_wb['3월 실적']

# 2. New workbook
wb = openpyxl.Workbook()

# ===== 사용법 sheet =====
ws_guide = wb.active
ws_guide.title = '사용법'
guide_lines = [
    '조립비 정산 수식 버전 — 사용법',
    '',
    '1. GERP_입력 시트에 G-ERP 실적 데이터를 붙여넣기 (헤더 포함, Row1부터)',
    '2. 구ERP_입력 시트에 구ERP 전체입고량 데이터를 붙여넣기 (헤더 포함, Row1부터)',
    '3. 각 라인 시트의 GERP/구ERP 실적·금액이 자동 계산됨',
    '4. 정산집계 시트에서 라인별 합계 확인',
    '',
    '※ 현재 3월 실적 데이터가 미리 입력되어 있음',
    '※ 다음 달 정산 시 GERP_입력/구ERP_입력만 새 데이터로 교체하면 자동 갱신',
    '',
    '수식 구조:',
    '  GERP 주간수량 = SUMIFS(생산량, 라인=해당라인, 품번=해당품번, 주야=정상)',
    '  GERP 야간수량 = SUMIFS(생산량, 라인=해당라인, 품번=해당품번, 주야=추가)',
    '  GERP 금액 = 기준단가 x 수량',
    '  SD9A01 야간금액 = 기준단가 x 0.3 x 야간수량 (야간 30% 가산)',
    '  구ERP 수량 = SUMIFS(입고수량, 품번=해당품번)',
    '',
    '제한사항:',
    '  - 구ERP 야간: LOT 끝자리 B = 야간, 그 외 = 주간',
    '  - SP3M3 구ERP: 서브라인 LOT B 무의미 → 총수량-GERP야간=주간, 야간=GERP야간',
    '  - SP3M3 RSP 모듈품번 역변환은 수식으로 불가 -> Python 파이프라인 필요',
    '  - Usage=2 품번 수량 2배 환산은 미적용 (필요시 수동 확인)',
]
for r, text in enumerate(guide_lines, 1):
    ws_guide.cell(r, 1, text)
ws_guide.cell(1, 1).font = Font(bold=True, size=14)
ws_guide.column_dimensions['A'].width = 80

# ===== GERP_입력 sheet =====
print("4. GERP_입력 시트 생성...")
ws_gerp = wb.create_sheet('GERP_입력')

gerp_row_count = 0
for r in range(1, gerp_ws.max_row + 1):
    for c in range(1, gerp_ws.max_column + 1):
        v = gerp_ws.cell(r, c).value
        cell = ws_gerp.cell(r, c, v)
        if r == 1:
            cell.font = header_font
            cell.fill = gerp_fill
            cell.border = thin_border
        elif isinstance(v, (int, float)):
            cell.number_format = num_fmt
    if r > 1:
        gerp_row_count += 1

print(f"   GERP 데이터: {gerp_row_count}행")

# ===== 구ERP_입력 sheet (품번별 주야 집계) =====
print("5. 구ERP_입력 시트 생성 (품번별 집계)...")
ws_olderp = wb.create_sheet('구ERP_입력')

# Python에서 0109 업체 품번별 주간/야간 수량 집계
from collections import defaultdict
olderp_day = defaultdict(int)   # LOT 끝자리 ≠ B
olderp_night = defaultdict(int) # LOT 끝자리 = B

olderp_raw_count = 0
for r in range(3, olderp_ws.max_row + 1):
    pn = olderp_ws.cell(r, 5).value
    vendor = olderp_ws.cell(r, 3).value
    if not pn or not vendor or not str(vendor).startswith('0109'):
        continue
    olderp_raw_count += 1
    lot = str(olderp_ws.cell(r, 10).value or '')
    qty = olderp_ws.cell(r, 11).value or 0
    if lot.strip().endswith('B'):
        olderp_night[pn] += qty
    else:
        olderp_day[pn] += qty

# 품번 합집합
all_pns = sorted(set(olderp_day) | set(olderp_night), key=str)

olderp_headers = ['품번', '주간수량', '야간수량', '합계']
for c, h in enumerate(olderp_headers, 1):
    cell = ws_olderp.cell(1, c, h)
    cell.font = header_font
    cell.fill = olderp_fill
    cell.border = thin_border

for i, pn in enumerate(all_pns):
    out_r = i + 2
    ws_olderp.cell(out_r, 1, pn)
    ws_olderp.cell(out_r, 2, olderp_day.get(pn, 0)).number_format = num_fmt
    ws_olderp.cell(out_r, 3, olderp_night.get(pn, 0)).number_format = num_fmt
    ws_olderp.cell(out_r, 4).value = f'=B{out_r}+C{out_r}'
    ws_olderp.cell(out_r, 4).number_format = num_fmt

print(f"   구ERP 원본: {olderp_raw_count}행 → 집계: {len(all_pns)}품번")

# ===== 10 Line sheets =====
LINES = ['SD9A01', 'ANAAS04', 'DRAAS11', 'SP3M3', 'HASMS02', 'HCAMS02',
         'WAMAS01', 'WABAS01', 'WASAS01', 'ISAMS03']

line_summaries = {}

for line in LINES:
    print(f"6. {line} 시트 생성...")
    ref_ws = ref_wb[line]
    ws = wb.create_sheet(line)

    # Row 1: section headers
    sections = [
        (1, 8, '기준정보', header_fill),
        (9, 10, 'GERP 실적', gerp_fill),
        (11, 12, 'GERP 금액', gerp_fill),
        (13, 14, '구ERP 실적', olderp_fill),
        (15, 16, '구ERP 금액', olderp_fill),
        (17, 18, '차이', summary_fill),
    ]
    for start, end, title, fill in sections:
        cell = ws.cell(1, start, title)
        cell.font = header_font
        cell.fill = fill
        cell.border = thin_border
        if start != end:
            ws.merge_cells(start_row=1, start_column=start, end_row=1, end_column=end)
            for cc in range(start + 1, end + 1):
                ws.cell(1, cc).fill = fill
                ws.cell(1, cc).border = thin_border

    # Row 2: column headers
    col_headers = ['품번', '조립업체코드', '조립라인코드', '조립품번', 'Usage',
                   '단가구분', '단가', '차종',
                   '주간', '야간', '주간', '야간',
                   '주간', '야간', '주간', '야간',
                   '금액차이', '수량차이']
    for c, h in enumerate(col_headers, 1):
        cell = ws.cell(2, c, h)
        cell.font = header_font
        cell.border = thin_border
        if c <= 8:
            cell.fill = header_fill
        elif c <= 12:
            cell.fill = gerp_fill
        elif c <= 16:
            cell.fill = olderp_fill
        else:
            cell.fill = summary_fill

    # Data rows (ref file: row 4+ = data, row 1=title, row 3=header)
    out_r = 2  # will increment to 3+
    for r in range(4, ref_ws.max_row + 1):
        pn = ref_ws.cell(r, 1).value
        if not pn:
            continue
        out_r += 1

        # A~H: 기준정보
        for c in range(1, 9):
            v = ref_ws.cell(r, c).value
            cell = ws.cell(out_r, c, v)
            cell.border = thin_border
            if c == 7 and isinstance(v, (int, float)):
                cell.number_format = num_fmt

        # I: GERP 주간수량
        ws.cell(out_r, 9).value = (
            f'=SUMIFS(GERP_입력!$I:$I,'
            f'GERP_입력!$C:$C,"{line}",'
            f'GERP_입력!$G:$G,A{out_r},'
            f'GERP_입력!$N:$N,"정상")')
        ws.cell(out_r, 9).number_format = num_fmt
        ws.cell(out_r, 9).border = thin_border

        # J: GERP 야간수량
        ws.cell(out_r, 10).value = (
            f'=SUMIFS(GERP_입력!$I:$I,'
            f'GERP_입력!$C:$C,"{line}",'
            f'GERP_입력!$G:$G,A{out_r},'
            f'GERP_입력!$N:$N,"추가")')
        ws.cell(out_r, 10).number_format = num_fmt
        ws.cell(out_r, 10).border = thin_border

        # K: GERP 주간금액
        ws.cell(out_r, 11).value = f'=G{out_r}*I{out_r}'
        ws.cell(out_r, 11).number_format = num_fmt
        ws.cell(out_r, 11).border = thin_border

        # L: GERP 야간금액 — GERP 추가행의 조립금액(col Q)을 직접 합산
        #    야간은 GERP 원본금액이 권위값이므로 기준단가로 재계산하지 않음
        ws.cell(out_r, 12).value = (
            f'=SUMIFS(GERP_입력!$Q:$Q,'
            f'GERP_입력!$C:$C,"{line}",'
            f'GERP_입력!$G:$G,A{out_r},'
            f'GERP_입력!$N:$N,"추가")')
        ws.cell(out_r, 12).number_format = num_fmt
        ws.cell(out_r, 12).border = thin_border

        # M: 구ERP 주간수량 — 집계 테이블에서 SUMIFS
        # SP3M3: 구ERP 총수량(합계) - GERP 야간수량 (서브라인 LOT B 무의미)
        if line == 'SP3M3':
            ws.cell(out_r, 13).value = (
                f'=IFERROR(SUMIFS('
                f"구ERP_입력!$D:$D,구ERP_입력!$A:$A,A{out_r}),0)"
                f'-J{out_r}')
        else:
            ws.cell(out_r, 13).value = (
                f'=IFERROR(SUMIFS('
                f"구ERP_입력!$B:$B,구ERP_입력!$A:$A,A{out_r}),0)")
        ws.cell(out_r, 13).number_format = num_fmt
        ws.cell(out_r, 13).border = thin_border

        # N: 구ERP 야간수량 — 집계 테이블에서 SUMIFS
        # SP3M3: GERP 야간 동일 적용 (서브라인 야간 구분 불가)
        if line == 'SP3M3':
            ws.cell(out_r, 14).value = f'=J{out_r}'
        else:
            ws.cell(out_r, 14).value = (
                f'=IFERROR(SUMIFS('
                f"구ERP_입력!$C:$C,구ERP_입력!$A:$A,A{out_r}),0)")
        ws.cell(out_r, 14).number_format = num_fmt
        ws.cell(out_r, 14).border = thin_border

        # O: 구ERP 주간금액
        ws.cell(out_r, 15).value = f'=G{out_r}*M{out_r}'
        ws.cell(out_r, 15).number_format = num_fmt
        ws.cell(out_r, 15).border = thin_border

        # P: 구ERP 야간금액
        ws.cell(out_r, 16).value = f'=G{out_r}*N{out_r}'
        ws.cell(out_r, 16).number_format = num_fmt
        ws.cell(out_r, 16).border = thin_border

        # Q: 금액차이
        ws.cell(out_r, 17).value = f'=(K{out_r}+L{out_r})-(O{out_r}+P{out_r})'
        ws.cell(out_r, 17).number_format = num_fmt
        ws.cell(out_r, 17).border = thin_border

        # R: 수량차이
        ws.cell(out_r, 18).value = f'=(I{out_r}+J{out_r})-(M{out_r}+N{out_r})'
        ws.cell(out_r, 18).number_format = num_fmt
        ws.cell(out_r, 18).border = thin_border

    last_r = out_r

    # Summary row
    sum_r = last_r + 1
    ws.cell(sum_r, 1, '합계').font = Font(bold=True)
    ws.cell(sum_r, 1).fill = summary_fill
    ws.cell(sum_r, 1).border = thin_border
    for c in range(9, 19):
        cl = get_column_letter(c)
        ws.cell(sum_r, c).value = f'=SUM({cl}3:{cl}{last_r})'
        ws.cell(sum_r, c).number_format = num_fmt
        ws.cell(sum_r, c).font = Font(bold=True)
        ws.cell(sum_r, c).fill = summary_fill
        ws.cell(sum_r, c).border = thin_border

    # SP3M3: 야간은 RSP 모듈품번이라 행별 매칭 불가 → 합계행에서 직접 SUMIFS
    if line == 'SP3M3':
        # J: 야간수량 합계 = GERP_입력에서 SP3M3 + 추가 행 전체
        ws.cell(sum_r, 10).value = (
            '=SUMIFS(GERP_입력!$I:$I,'
            'GERP_입력!$C:$C,"SP3M3",'
            'GERP_입력!$N:$N,"추가")')
        # L: 야간금액 합계 = GERP_입력 조립금액에서 SP3M3 + 추가
        ws.cell(sum_r, 12).value = (
            '=SUMIFS(GERP_입력!$Q:$Q,'
            'GERP_입력!$C:$C,"SP3M3",'
            'GERP_입력!$N:$N,"추가")')

    line_summaries[line] = sum_r

    # Column widths
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['D'].width = 16
    for c in range(9, 19):
        ws.column_dimensions[get_column_letter(c)].width = 14

    print(f"   {line}: data rows={last_r - 2}, sum_row={sum_r}")

# ===== 정산집계 sheet =====
print("7. 정산집계 시트 생성...")
ws_sum = wb.create_sheet('정산집계')

sum_headers = ['라인코드', '라인명',
               'GERP주간수량', 'GERP야간수량', 'GERP주간금액', 'GERP야간금액', 'GERP합계',
               '구ERP주간수량', '구ERP야간수량', '구ERP주간금액', '구ERP야간금액', '구ERP합계',
               '금액차이']
line_names = {
    'SD9A01': '아우터', 'ANAAS04': '앵커', 'DRAAS11': '디링',
    'SP3M3': 'SP3', 'HASMS02': 'HASMS', 'HCAMS02': 'HCAMS',
    'WAMAS01': '웨빙', 'WABAS01': '웨빙버클', 'WASAS01': 'WASAS',
    'ISAMS03': '이너센스'
}

for c, h in enumerate(sum_headers, 1):
    cell = ws_sum.cell(1, c, h)
    cell.font = header_font
    cell.fill = header_fill
    cell.border = thin_border

for i, line in enumerate(LINES):
    r = i + 2
    sr = line_summaries[line]

    ws_sum.cell(r, 1, line).border = thin_border
    ws_sum.cell(r, 2, line_names.get(line, line)).border = thin_border

    # GERP: I=주간수량, J=야간수량, K=주간금액, L=야간금액
    ws_sum.cell(r, 3).value = f"='{line}'!I{sr}"
    ws_sum.cell(r, 4).value = f"='{line}'!J{sr}"
    ws_sum.cell(r, 5).value = f"='{line}'!K{sr}"
    ws_sum.cell(r, 6).value = f"='{line}'!L{sr}"
    ws_sum.cell(r, 7).value = f'=E{r}+F{r}'

    # 구ERP: M=주간수량, N=야간수량, O=주간금액, P=야간금액
    ws_sum.cell(r, 8).value = f"='{line}'!M{sr}"
    ws_sum.cell(r, 9).value = f"='{line}'!N{sr}"
    ws_sum.cell(r, 10).value = f"='{line}'!O{sr}"
    ws_sum.cell(r, 11).value = f"='{line}'!P{sr}"
    ws_sum.cell(r, 12).value = f'=J{r}+K{r}'

    # 금액차이
    ws_sum.cell(r, 13).value = f'=G{r}-L{r}'
    ws_sum.cell(r, 13).font = Font(bold=True, color='FF0000')

    for c in range(3, 14):
        ws_sum.cell(r, c).number_format = num_fmt
        ws_sum.cell(r, c).border = thin_border
    ws_sum.cell(r, 7).font = Font(bold=True)
    ws_sum.cell(r, 12).font = Font(bold=True)

# Total row
total_r = len(LINES) + 2
ws_sum.cell(total_r, 1, '합계').font = Font(bold=True, size=12)
ws_sum.cell(total_r, 1).fill = summary_fill
ws_sum.cell(total_r, 1).border = thin_border
ws_sum.cell(total_r, 2).fill = summary_fill
ws_sum.cell(total_r, 2).border = thin_border
for c in range(3, 14):
    cl = get_column_letter(c)
    ws_sum.cell(total_r, c).value = f'=SUM({cl}2:{cl}{total_r - 1})'
    ws_sum.cell(total_r, c).number_format = num_fmt
    ws_sum.cell(total_r, c).font = Font(bold=True, size=12)
    ws_sum.cell(total_r, c).fill = summary_fill
    ws_sum.cell(total_r, c).border = thin_border

ws_sum.column_dimensions['A'].width = 12
ws_sum.column_dimensions['B'].width = 10
for c in range(3, 14):
    ws_sum.column_dimensions[get_column_letter(c)].width = 16

# Save
output = os.path.join(BASE, '04월', '정산_수식버전_03월.xlsx')
wb.save(output)
print(f"\n=== 완료: {output} ===")
print(f"시트: {wb.sheetnames}")
print(f"총 {len(wb.sheetnames)}개 시트")
