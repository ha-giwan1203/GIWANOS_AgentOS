"""
VBA 모듈 자동 주입 스크립트
modPlanResultFixed 모듈을 _v2.xlsm에서 교체한다.
"""
import win32com.client
import os
import time

XLSM_PATH = os.path.abspath("SP3M3_생산지시서_메크로자동화_v2.xlsm")
BAS_PATH = os.path.abspath("modPlanResultFixed_modified.bas")
MODULE_NAME = "modPlanResultFixed"

if not os.path.exists(XLSM_PATH):
    raise FileNotFoundError(f"xlsm not found: {XLSM_PATH}")
if not os.path.exists(BAS_PATH):
    raise FileNotFoundError(f"bas not found: {BAS_PATH}")

print(f"Target: {XLSM_PATH}")
print(f"Module: {BAS_PATH}")

excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False

try:
    wb = excel.Workbooks.Open(XLSM_PATH)
    vbproj = wb.VBProject

    # 기존 모듈 삭제
    found = False
    for comp in vbproj.VBComponents:
        if comp.Name == MODULE_NAME:
            print(f"기존 모듈 '{MODULE_NAME}' 발견 → 삭제")
            vbproj.VBComponents.Remove(comp)
            found = True
            break

    if not found:
        print(f"기존 모듈 '{MODULE_NAME}' 없음 — 신규 import 진행")

    # 새 모듈 import
    vbproj.VBComponents.Import(BAS_PATH)
    print(f"모듈 '{MODULE_NAME}' import 완료")

    # 주입된 모듈 확인
    imported = False
    for comp in vbproj.VBComponents:
        if comp.Name == MODULE_NAME:
            line_count = comp.CodeModule.CountOfLines
            print(f"검증: '{MODULE_NAME}' 존재, {line_count} lines")
            imported = True
            break

    if not imported:
        # import 시 이름이 달라질 수 있음 (modPlanResultFixed_modified)
        for comp in vbproj.VBComponents:
            if "modPlanResultFixed" in comp.Name:
                print(f"검증: '{comp.Name}' 존재 (이름 확인 필요), {comp.CodeModule.CountOfLines} lines")
                # 이름 변경
                if comp.Name != MODULE_NAME:
                    comp.Name = MODULE_NAME
                    print(f"이름 변경: → '{MODULE_NAME}'")
                imported = True
                break

    if not imported:
        print("ERROR: import 후 모듈을 찾을 수 없음")

    # 저장
    wb.Save()
    print("파일 저장 완료")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    try:
        wb.Close(False)
    except:
        pass
    excel.Quit()
    print("Excel 종료")
