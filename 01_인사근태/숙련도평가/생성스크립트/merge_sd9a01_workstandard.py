"""
SD9A01 작업표준서 통합본 작성 (Phase 1)

입력:
  - SD9A01_표준문서/SD9A01 작업표준서(180706) Rev.16.xls (17 sheets)
  - SD9A01_표준문서/SD9A01 작업표준서(260101) Rev.16.xls (13 sheets)

출력:
  - SD9A01_표준문서/SD9A01 작업표준서 통합_Rev16.xlsx

전략:
  - 260101이 최신 → 베이스로 .xlsx 변환 후 사본 저장
  - 180706 단독 시트(20/81/82/83) → 통합본에 복사 (Excel COM)
  - 시트 순서: 표지 / D9 PT 곡률이력 / 20 / 21 / 30 / 40 / 43 / 50 / 60 / 70 / 80 / 81 / 82 / 83 / 90 / 100 / 카메라

도구: pywin32 (Excel COM) — 한글 시트명·셀병합·서식 보존을 위해 Excel 직접 호출.
"""
import os
import sys
import time
import shutil
import win32com.client as win32

BASE = r'C:\Users\User\Desktop\업무리스트\01_인사근태\숙련도평가\SD9A01_표준문서'
SRC_OLD = os.path.join(BASE, 'SD9A01 작업표준서(180706) Rev.16.xls')
SRC_NEW = os.path.join(BASE, 'SD9A01 작업표준서(260101) Rev.16.xls')
OUT     = os.path.join(BASE, 'SD9A01 작업표준서 통합_Rev16.xlsx')

# 통합본 최종 시트 순서 (한글 시트명은 실제 파일에서 그대로 가져옴)
# 숫자 시트는 직접 비교, 표지/D9 PT/카메라 같은 한글 시트는 검출 후 처리
TARGET_ORDER_NUM = ['20', '21', '30', '40', '43', '50', '60', '70', '80', '81', '82', '83', '90', '100']

OLD_ONLY_NUM = ['20', '81', '82', '83']  # 180706에만 있는 숫자 시트
NEW_BASE_NUM = ['21', '30', '40', '43', '50', '60', '70', '80', '90', '100']  # 260101 베이스


def _msg(s): print(f'[merge] {s}', flush=True)


def main():
    if not os.path.exists(SRC_OLD):
        sys.exit(f'NOT FOUND: {SRC_OLD}')
    if not os.path.exists(SRC_NEW):
        sys.exit(f'NOT FOUND: {SRC_NEW}')

    if os.path.exists(OUT):
        bak = OUT + f'.bak.{int(time.time())}'
        shutil.move(OUT, bak)
        _msg(f'기존 통합본 백업: {os.path.basename(bak)}')

    excel = win32.Dispatch('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    tmp_dir = os.path.join(BASE, '_tmp_xlsx')
    os.makedirs(tmp_dir, exist_ok=True)
    OLD_XLSX = os.path.join(tmp_dir, '180706.xlsx')
    NEW_XLSX = os.path.join(tmp_dir, '260101.xlsx')

    try:
        # 1) 두 .xls를 모두 .xlsx로 변환 (sheet copy 호환 확보)
        for src, dst in [(SRC_OLD, OLD_XLSX), (SRC_NEW, NEW_XLSX)]:
            _msg(f'변환: {os.path.basename(src)} → {os.path.basename(dst)}')
            if os.path.exists(dst): os.remove(dst)
            wb = excel.Workbooks.Open(src, ReadOnly=True)
            wb.SaveAs(dst, FileFormat=51)
            wb.Close(SaveChanges=False)

        # 2) 260101.xlsx를 통합본으로 복사
        shutil.copyfile(NEW_XLSX, OUT)
        _msg(f'통합본 베이스: 260101.xlsx → 통합_Rev16.xlsx')

        # 3) 통합본 + 변환된 180706 열기 → 단독 시트 복사
        wb_out = excel.Workbooks.Open(OUT)
        wb_old = excel.Workbooks.Open(OLD_XLSX, ReadOnly=False)

        out_sheets = [wb_out.Sheets(i+1).Name for i in range(wb_out.Sheets.Count)]
        _msg(f'통합본 베이스 시트({len(out_sheets)})')
        for n in out_sheets: _msg(f'  base: [{n}]')

        old_sheets = [wb_old.Sheets(i+1).Name for i in range(wb_old.Sheets.Count)]
        _msg(f'180706 시트({len(old_sheets)})')
        for n in old_sheets: _msg(f'  old : [{n}]')

        # 180706에만 있는 숫자 시트 복사 (wb_out.Activate → Copy(Before=wb_out.Sheets(1)))
        wb_out.Activate()
        for sname in OLD_ONLY_NUM:
            if sname not in old_sheets:
                _msg(f'  SKIP: 180706에 시트 [{sname}] 없음')
                continue
            try:
                before_count = wb_out.Sheets.Count
                # 명시적으로 Worksheets 컬렉션 + 통합본 활성화 후 Before=Worksheets(1)
                wb_out.Activate()
                wb_old.Worksheets(sname).Copy(Before=wb_out.Worksheets(1))
                # 복사 후 ActiveWorkbook이 wb_out인지 확인
                actv = excel.ActiveWorkbook
                actv_name = actv.Name if actv else 'None'
                after_count = wb_out.Sheets.Count
                old_after = wb_old.Sheets.Count
                _msg(f'  + 시트 [{sname}] copy → wb_out:{before_count}→{after_count} / wb_old:{old_after} / active=[{actv_name}]')
            except Exception as e:
                _msg(f'  FAIL 시트 [{sname}] 복사: {e}')

        # 4) 시트 정렬
        all_after = [wb_out.Sheets(i+1).Name for i in range(wb_out.Sheets.Count)]
        _msg(f'복사 후 통합본 시트({len(all_after)})')
        for n in all_after: _msg(f'  after: [{n}]')

        cover = next((n for n in all_after if any(k in n for k in ('표지', '목록', '커버', 'INDEX', 'index'))), None)
        ptcurve = next((n for n in all_after if 'PT' in n.upper() and ('곡률' in n or 'D9' in n)), None)
        camera = next((n for n in all_after if '카메라' in n), None)
        _msg(f'  detect cover=[{cover}] ptcurve=[{ptcurve}] camera=[{camera}]')

        desired_order = []
        if cover: desired_order.append(cover)
        if ptcurve: desired_order.append(ptcurve)
        for n in TARGET_ORDER_NUM:
            if n in all_after: desired_order.append(n)
        if camera: desired_order.append(camera)
        for n in all_after:
            if n not in desired_order:
                desired_order.append(n)
                _msg(f'  TAIL: {n}')

        _msg(f'desired_order({len(desired_order)}): {desired_order}')

        # 정렬: 처음부터 차례대로 Before(i+1)로 이동
        for i, sname in enumerate(desired_order):
            try:
                tgt_pos = i + 1
                cur_idx = None
                for j in range(wb_out.Sheets.Count):
                    if wb_out.Sheets(j+1).Name == sname:
                        cur_idx = j + 1
                        break
                if cur_idx is None:
                    _msg(f'  ORDER: skip [{sname}] — not found')
                    continue
                if cur_idx == tgt_pos:
                    continue
                if tgt_pos > wb_out.Sheets.Count:
                    wb_out.Sheets(sname).Move(After=wb_out.Sheets(wb_out.Sheets.Count))
                else:
                    wb_out.Sheets(sname).Move(Before=wb_out.Sheets(tgt_pos))
            except Exception as e:
                _msg(f'  ORDER FAIL [{sname}]: {e}')

        final_order = [wb_out.Sheets(i+1).Name for i in range(wb_out.Sheets.Count)]
        _msg(f'final({len(final_order)}): {final_order}')

        wb_out.Save()
        wb_old.Close(SaveChanges=False)
        wb_out.Close(SaveChanges=False)
        _msg('OK 통합본 저장 완료')
        _msg(f'경로: {OUT}')

    finally:
        excel.Quit()

    # 임시 .xlsx 정리
    try:
        for f in (OLD_XLSX, NEW_XLSX):
            if os.path.exists(f): os.remove(f)
        if os.path.isdir(tmp_dir) and not os.listdir(tmp_dir):
            os.rmdir(tmp_dir)
        _msg('임시 변환 파일 정리 OK')
    except Exception as e:
        _msg(f'임시 정리 WARN: {e}')


if __name__ == '__main__':
    main()
