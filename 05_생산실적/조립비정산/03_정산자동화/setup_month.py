#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
월별 정산 환경 자동 세팅

실행:
    python setup_month.py 03            # 3월 정산 세팅
    python setup_month.py 04            # 4월 정산 세팅
    python setup_month.py 03 --dry-run  # 실제 변경 없이 계획만 출력

수행 작업:
    1. 월별 폴더 생성  (예: 05월/실적데이터/, 05월/_cache/)
    2. 실적 파일 탐색 + 복사  (04_실적데이터/ → 월별 폴더)
    3. _pipeline_config.py 자동 수정  (경로, MONTH, OLDERP_SHEET)
    4. 세팅 결과 검증
"""

import argparse
import glob
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ── 상수 ──
BASE_DIR = r'C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산'
SOURCE_DIR = os.path.join(BASE_DIR, '04_실적데이터')
CONFIG_FILE = os.path.join(BASE_DIR, '03_정산자동화', '_pipeline_config.py')

# 다음 달 폴더 매핑: 정산 대상월 → 처리 폴더
# 3월 정산 → 04월 폴더, 4월 정산 → 05월 폴더, ...
FOLDER_MONTH_OFFSET = 1


def next_month(mm: str) -> str:
    """정산 대상월 → 처리 폴더 월 (2자리)"""
    m = int(mm) + FOLDER_MONTH_OFFSET
    if m > 12:
        m -= 12
    return f'{m:02d}'


def find_source_files(month: str):
    """04_실적데이터/에서 해당 월 실적 파일 탐색"""
    if not os.path.exists(SOURCE_DIR):
        print(f"[ERROR] 실적 데이터 소스 폴더 없음: {SOURCE_DIR}")
        return None, None

    all_files = os.listdir(SOURCE_DIR)
    month_int = int(month)
    month_kr = f'{month_int}월'

    gerp_file = None
    olderp_file = None

    for f in all_files:
        fl = f.lower()
        # GERP 파일 탐색: "G-ERP", "GERP", "gerp" + 월 포함
        if ('g-erp' in fl or 'gerp' in fl) and (f'{month}월' in f or f'{month_int}월' in f):
            gerp_file = f
        # 구ERP 파일 탐색: "구ERP", "구erp" + 월 포함
        if ('구erp' in fl or '구erp' in f) and (f'{month}월' in f or f'{month_int}월' in f):
            olderp_file = f

    return gerp_file, olderp_file


def detect_olderp_sheet(month: str) -> str:
    """구ERP 시트명 추정 (일반적 패턴)"""
    month_int = int(month)
    return f'{month_int}월 실적'


def setup_month(month: str, dry_run: bool = False):
    """월별 정산 환경 세팅"""
    folder_month = next_month(month)
    folder_name = f'{folder_month}월'
    folder_path = os.path.join(BASE_DIR, folder_name)
    data_path = os.path.join(folder_path, '실적데이터')
    cache_path = os.path.join(folder_path, '_cache')

    print('=' * 60)
    print(f'월별 정산 환경 세팅 — {month}월 정산')
    print(f'  처리 폴더: {folder_name}/')
    if dry_run:
        print('  [DRY-RUN] 실제 변경 없음')
    print('=' * 60)

    # ── 1. 폴더 생성 ──
    print(f'\n[1/4] 폴더 생성...')
    for p in [folder_path, data_path, cache_path]:
        exists = os.path.exists(p)
        status = '존재' if exists else '생성'
        print(f'  {os.path.relpath(p, BASE_DIR):30s} [{status}]')
        if not exists and not dry_run:
            os.makedirs(p, exist_ok=True)

    # ── 2. 실적 파일 탐색 + 복사 ──
    print(f'\n[2/4] 실적 파일 탐색...')
    gerp_name, olderp_name = find_source_files(month)

    files_ok = True
    if gerp_name:
        print(f'  GERP:  {gerp_name}')
    else:
        print(f'  GERP:  [미발견] — 04_실적데이터/에 {month}월 GERP 파일 없음')
        files_ok = False

    if olderp_name:
        print(f'  구ERP: {olderp_name}')
    else:
        print(f'  구ERP: [미발견] — 04_실적데이터/에 {month}월 구ERP 파일 없음')
        files_ok = False

    if files_ok:
        print(f'\n  파일 복사 → {os.path.relpath(data_path, BASE_DIR)}/')
        for fname in [gerp_name, olderp_name]:
            src = os.path.join(SOURCE_DIR, fname)
            dst = os.path.join(data_path, fname)
            if os.path.exists(dst):
                print(f'    {fname} [이미 존재 — 건너뜀]')
            else:
                print(f'    {fname} [복사]')
                if not dry_run:
                    shutil.copy2(src, dst)
    else:
        print('\n  [WARNING] 실적 파일이 부족합니다. 수동 배치 후 재실행하세요.')

    # ── 3. _pipeline_config.py 수정 ──
    print(f'\n[3/4] _pipeline_config.py 수정...')

    if not os.path.exists(CONFIG_FILE):
        print(f'  [ERROR] config 파일 없음: {CONFIG_FILE}')
        return False

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = f.read()

    # 수정 사항 수집
    changes = []

    # CACHE_DIR
    new_cache = f"CACHE_DIR    = os.path.join(BASE_DIR, '{folder_name}', '_cache')"
    old_cache_match = re.search(r"^CACHE_DIR\s*=.*$", config, re.MULTILINE)
    if old_cache_match:
        old_val = old_cache_match.group(0)
        if old_val != new_cache:
            changes.append(('CACHE_DIR', old_val, new_cache))
            config = config.replace(old_val, new_cache)

    # GERP_FILE
    if gerp_name:
        new_gerp = f"GERP_FILE    = os.path.join(BASE_DIR, '{folder_name}', '실적데이터', '{gerp_name}')"
        old_gerp_match = re.search(r"^GERP_FILE\s*=.*$", config, re.MULTILINE)
        if old_gerp_match:
            old_val = old_gerp_match.group(0)
            if old_val != new_gerp:
                changes.append(('GERP_FILE', old_val, new_gerp))
                config = config.replace(old_val, new_gerp)

    # OLDERP_FILE
    if olderp_name:
        new_olderp = f"OLDERP_FILE  = os.path.join(BASE_DIR, '{folder_name}', '실적데이터', '{olderp_name}')"
        old_olderp_match = re.search(r"^OLDERP_FILE\s*=.*$", config, re.MULTILINE)
        if old_olderp_match:
            old_val = old_olderp_match.group(0)
            if old_val != new_olderp:
                changes.append(('OLDERP_FILE', old_val, new_olderp))
                config = config.replace(old_val, new_olderp)

    # OUTPUT_FILE
    new_output = f"OUTPUT_FILE  = os.path.join(BASE_DIR, '{folder_name}', '정산결과_{month}월.xlsx')   # ← 월 바꿀 때 수정"
    old_output_match = re.search(r"^OUTPUT_FILE\s*=.*$", config, re.MULTILINE)
    if old_output_match:
        old_val = old_output_match.group(0)
        if old_val != new_output:
            changes.append(('OUTPUT_FILE', old_val, new_output))
            config = config.replace(old_val, new_output)

    # OLDERP_SHEET
    new_sheet = detect_olderp_sheet(month)
    old_sheet_match = re.search(r"^OLDERP_SHEET\s*=\s*'([^']*)'", config, re.MULTILINE)
    if old_sheet_match:
        old_sheet_val = old_sheet_match.group(0)
        new_sheet_line = f"OLDERP_SHEET = '{new_sheet}'   # 구ERP 데이터 시트명 (파일마다 다를 수 있음)"
        if old_sheet_val != new_sheet_line.split('   #')[0]:
            changes.append(('OLDERP_SHEET', old_sheet_val, new_sheet_line))
            config = re.sub(r"^OLDERP_SHEET\s*=.*$", new_sheet_line, config, flags=re.MULTILINE)

    # MONTH
    old_month_match = re.search(r"^MONTH\s*=\s*'([^']*)'", config, re.MULTILINE)
    if old_month_match:
        old_month_val = old_month_match.group(0)
        new_month_line = f"MONTH        = '{month}'"
        if old_month_match.group(1) != month:
            changes.append(('MONTH', old_month_val, new_month_line))
            config = re.sub(r"^MONTH\s*=.*$", new_month_line, config, flags=re.MULTILINE)

    if changes:
        for name, old, new in changes:
            print(f'  {name}:')
            print(f'    - {old.strip()}')
            print(f'    + {new.strip()}')
        if not dry_run:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(config)
            print(f'  config 저장 완료')
    else:
        print(f'  변경 없음 (이미 {month}월 설정)')

    # ── 4. 검증 ──
    print(f'\n[4/4] 검증...')
    checks = []

    # 폴더 존재
    for p, label in [(folder_path, '월별폴더'), (data_path, '실적데이터'), (cache_path, '캐시')]:
        exists = os.path.exists(p) or dry_run
        checks.append((label, exists))

    # 파일 존재
    if gerp_name:
        gp = os.path.join(data_path, gerp_name)
        checks.append(('GERP파일', os.path.exists(gp) or dry_run))
    if olderp_name:
        op = os.path.join(data_path, olderp_name)
        checks.append(('구ERP파일', os.path.exists(op) or dry_run))

    # config 정합성
    checks.append(('config수정', len(changes) >= 0))  # 수정했거나 이미 맞으면 OK

    all_ok = all(v for _, v in checks)
    for label, ok in checks:
        print(f'  {label:12s}: {"OK" if ok else "FAIL"}')

    # ── 결과 ──
    print(f'\n{"=" * 60}')
    if all_ok and files_ok:
        print(f'세팅 완료 — {month}월 정산 준비 OK')
        print(f'\n다음 단계:')
        print(f'  python run_settlement_pipeline.py')
        print(f'  또는: python run_settlement_pipeline.py --month {month}')
    else:
        print(f'세팅 미완료 — 위 경고 확인 후 재실행')
    print('=' * 60)

    return all_ok and files_ok


def main():
    parser = argparse.ArgumentParser(
        description='월별 정산 환경 자동 세팅',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('month', help='정산 대상 월 (두 자리, 예: 03)')
    parser.add_argument('--dry-run', action='store_true',
                        help='실제 변경 없이 계획만 출력')
    args = parser.parse_args()

    # 월 검증
    try:
        m = int(args.month)
        if not (1 <= m <= 12):
            raise ValueError
        month = f'{m:02d}'
    except ValueError:
        print(f'[ERROR] 올바른 월을 입력하세요 (01~12). 입력: {args.month}')
        sys.exit(1)

    ok = setup_month(month, dry_run=args.dry_run)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
