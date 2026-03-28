#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조립비 정산 파이프라인 단일 실행기

Step 1~7을 순차 실행하며, 실패 시 즉시 중단.
로그와 요약 JSON을 run_logs/ 폴더에 저장한다.

사용법:
    python run_settlement_pipeline.py
    python run_settlement_pipeline.py --start-from 3
    python run_settlement_pipeline.py --use-cache
    python run_settlement_pipeline.py --month 04
    python run_settlement_pipeline.py --start-from 5 --use-cache --month 03

옵션:
    --start-from N   Step N부터 재시작 (1~7, 기본값: 1)
    --use-cache      이전 _cache/ JSON이 있는 Step은 건너뜀
    --month MM       대상 월 (두 자리 예: 03). _pipeline_config.py의 MONTH 및
                     OUTPUT_FILE 월 부분을 실행 전에 임시 교체하고 복원한다.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

# ── 상수 ──────────────────────────────────────────────────────
PYTHON = r'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, 'run_logs')
CONFIG_FILE = os.path.join(SCRIPT_DIR, '_pipeline_config.py')

# Step 번호 → 스크립트 파일명
STEP_SCRIPTS = {
    1: 'step1_파일검증.py',
    2: 'step2_gerp처리.py',
    3: 'step3_구erp처리.py',
    4: 'step4_기준정보매칭.py',
    5: 'step5_정산계산.py',
    6: 'step6_검증.py',
    7: 'step7_보고서.py',
}

# Step별 출력 캐시 파일 (--use-cache 판단용)
STEP_OUTPUTS = {
    1: os.path.join(SCRIPT_DIR, '_cache', 'step1_validation.json'),
    2: os.path.join(SCRIPT_DIR, '_cache', 'step2_gerp.json'),
    3: os.path.join(SCRIPT_DIR, '_cache', 'step3_olderp.json'),
    4: os.path.join(SCRIPT_DIR, '_cache', 'step4_matched.json'),
    5: os.path.join(SCRIPT_DIR, '_cache', 'step5_settlement.json'),
    6: os.path.join(SCRIPT_DIR, '_cache', 'step6_validation.json'),
    7: None,  # Step 7 출력은 OUTPUT_FILE (설정값 읽기 필요)
}

# Step 완료 후 권장 도메인 에이전트 (1·3·5는 해당 없음)
STEP_AGENT_RECOMMENDATIONS = {
    2: 'gerp-processor 에이전트로 GERP 데이터 품질 점검 권장',
    4: 'reference-matcher 에이전트로 매칭 결과 검토 권장',
    6: 'settlement-validator 에이전트로 최종 판정 권장',
    7: 'report-writer 에이전트로 보고서 정리 권장',
}


# ── 인수 파싱 ──────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description='조립비 정산 파이프라인 실행기',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--start-from', type=int, default=1, metavar='N',
        help='Step N부터 시작 (1~7, 기본값: 1)',
    )
    parser.add_argument(
        '--use-cache', action='store_true',
        help='출력 파일이 이미 있는 Step은 건너뜀',
    )
    parser.add_argument(
        '--month', type=str, default=None, metavar='MM',
        help='대상 월 두 자리 (예: 03). 미지정 시 config 기본값 사용.',
    )
    return parser.parse_args()


# ── config 월 교체 ─────────────────────────────────────────────
class ConfigMonthPatch:
    """
    --month 옵션 사용 시 _pipeline_config.py의 MONTH 및 OUTPUT_FILE 월을
    실행 기간 동안 임시 교체하고, 종료 시 원본을 복원한다.
    """

    def __init__(self, month: str):
        self.month = month
        self.backup_path = CONFIG_FILE + '.pipeline_bak'
        self.patched = False

    def patch(self):
        if not os.path.exists(CONFIG_FILE):
            raise FileNotFoundError(f"config 파일 없음: {CONFIG_FILE}")
        shutil.copy2(CONFIG_FILE, self.backup_path)

        with open(CONFIG_FILE, encoding='utf-8') as f:
            content = f.read()

        # MONTH = '기존값' 교체
        content = re.sub(
            r"^(MONTH\s*=\s*')[^']*(')",
            rf"\g<1>{self.month}\2",
            content,
            flags=re.MULTILINE,
        )
        # OUTPUT_FILE 안의 월 표기 교체: 정산결과_XX월 → 정산결과_MM월
        content = re.sub(
            r"(정산결과_)\d{2}(월\.xlsx)",
            rf"\g<1>{self.month}\2",
            content,
        )

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(content)

        self.patched = True
        print(f"[config] MONTH → '{self.month}' 임시 적용")

    def restore(self):
        if self.patched and os.path.exists(self.backup_path):
            shutil.copy2(self.backup_path, CONFIG_FILE)
            os.remove(self.backup_path)
            self.patched = False
            print(f"[config] _pipeline_config.py 원본 복원 완료")


# ── Step 7 출력 경로 읽기 ──────────────────────────────────────
def get_step7_output() -> str:
    """_pipeline_config.py에서 OUTPUT_FILE 값을 동적으로 읽는다."""
    try:
        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        result = subprocess.run(
            [PYTHON, '-c',
             'import sys; sys.path.insert(0, r"{}"); '
             'from _pipeline_config import OUTPUT_FILE; print(OUTPUT_FILE)'.format(SCRIPT_DIR)],
            capture_output=True, text=True, encoding='utf-8',
            env=env,
        )
        return result.stdout.strip()
    except Exception:
        return ''


# ── Step 실행 ─────────────────────────────────────────────────
def run_step(step_no: int, script_name: str, log_file, skipped: bool = False) -> dict:
    start = datetime.now()
    divider = '─' * 60
    recommendation = STEP_AGENT_RECOMMENDATIONS.get(step_no)

    if skipped:
        msg = f"[{start.strftime('%H:%M:%S')}] Step {step_no}: {script_name}  [SKIP — cache 사용]"
        print(f"\n{divider}\n{msg}\n{divider}")
        log_file.write(f"\n{divider}\n{msg}\n{divider}\n")
        if recommendation:
            rec_msg = f"[권장 에이전트] {recommendation}\n"
            print(rec_msg, end='')
            log_file.write(rec_msg)
        log_file.flush()
        return {
            'step': step_no,
            'script': script_name,
            'status': 'SKIPPED',
            'exit_code': 0,
            'elapsed_sec': 0.0,
            'start': start.isoformat(),
            'end': start.isoformat(),
            'agent_recommendation': recommendation,
        }

    header = f"[{start.strftime('%H:%M:%S')}] Step {step_no}: {script_name} 시작"
    print(f"\n{divider}\n{header}\n{divider}")
    log_file.write(f"\n{'=' * 60}\nStep {step_no}: {script_name}\n시작: {start.isoformat()}\n{'=' * 60}\n")
    log_file.flush()

    script_path = os.path.join(SCRIPT_DIR, script_name)
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    proc = subprocess.run(
        [PYTHON, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=env,
    )

    end = datetime.now()
    elapsed = (end - start).total_seconds()

    # 콘솔 출력 + 로그 기록
    print(proc.stdout, end='')
    log_file.write(proc.stdout)

    status = 'SUCCESS' if proc.returncode == 0 else 'FAILED'
    footer = f"\nStep {step_no} {status}  (exit={proc.returncode}, {elapsed:.1f}s)\n"
    print(footer)
    log_file.write(footer)

    if recommendation and proc.returncode == 0:
        rec_msg = f"[권장 에이전트] {recommendation}\n"
        print(rec_msg, end='')
        log_file.write(rec_msg)

    log_file.flush()

    return {
        'step': step_no,
        'script': script_name,
        'status': status,
        'exit_code': proc.returncode,
        'elapsed_sec': round(elapsed, 2),
        'start': start.isoformat(),
        'end': end.isoformat(),
        'agent_recommendation': recommendation,
    }


# ── 캐시 파일 존재 여부 ────────────────────────────────────────
def has_cache(step_no: int) -> bool:
    output = STEP_OUTPUTS.get(step_no)
    if output is None:
        # Step 7: OUTPUT_FILE 경로를 동적으로 확인
        output = get_step7_output()
    if not output:
        return False
    return os.path.exists(output)


# ── 메인 ──────────────────────────────────────────────────────
def main():
    args = parse_args()

    # start-from 범위 검사
    if not (1 <= args.start_from <= 7):
        print(f"[ERROR] --start-from 값은 1~7이어야 합니다. (입력: {args.start_from})")
        sys.exit(1)

    # 월 패치 객체 (--month 미지정이면 None)
    month_patch = ConfigMonthPatch(args.month) if args.month else None

    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    log_path = os.path.join(LOG_DIR, f'{ts}.log')
    summary_path = os.path.join(LOG_DIR, f'{ts}_summary.json')

    pipeline_start = datetime.now()
    banner = (
        f"{'=' * 60}\n"
        f"조립비 정산 파이프라인\n"
        f"시작: {pipeline_start.isoformat()}\n"
        f"--start-from: {args.start_from}  "
        f"--use-cache: {args.use_cache}  "
        f"--month: {args.month or '(config 기본값)'}\n"
        f"로그: {log_path}\n"
        f"{'=' * 60}"
    )
    print(banner)

    step_results = []
    failed_step = None

    try:
        # 월 임시 패치 적용
        if month_patch:
            month_patch.patch()

        with open(log_path, 'w', encoding='utf-8') as lf:
            lf.write(banner + '\n')

            steps_to_run = [
                (n, s) for n, s in STEP_SCRIPTS.items()
                if n >= args.start_from
            ]

            for step_no, script_name in steps_to_run:
                # --use-cache: 출력 파일이 이미 존재하면 건너뜀
                skip = args.use_cache and has_cache(step_no)
                result = run_step(step_no, script_name, lf, skipped=skip)
                step_results.append(result)

                if result['exit_code'] != 0:
                    failed_step = step_no
                    msg = f"\n[FAILED] Step {step_no} 실패 — 파이프라인 중단\n"
                    print(msg)
                    lf.write(msg)
                    break

    finally:
        # 월 패치 복원 (실패해도 반드시 복원)
        if month_patch:
            month_patch.restore()

    # 결과 집계
    pipeline_end = datetime.now()
    total_elapsed = (pipeline_end - pipeline_start).total_seconds()
    overall = 'SUCCESS' if failed_step is None else f'FAILED at Step {failed_step}'

    step_agent_recommendations = {
        str(r['step']): r['agent_recommendation']
        for r in step_results
        if r.get('agent_recommendation')
    }

    summary = {
        'pipeline_status': overall,
        'start': pipeline_start.isoformat(),
        'end': pipeline_end.isoformat(),
        'total_elapsed_sec': round(total_elapsed, 2),
        'month': args.month,
        'start_from': args.start_from,
        'use_cache': args.use_cache,
        'failed_step': failed_step,
        'steps': step_results,
        'step_agent_recommendations': step_agent_recommendations,
        'log_file': log_path,
    }
    with open(summary_path, 'w', encoding='utf-8') as sf:
        json.dump(summary, sf, ensure_ascii=False, indent=2)

    # 최종 출력
    border = '=' * 60
    final = (
        f"\n{border}\n"
        f"파이프라인 완료\n"
        f"결과:  {overall}\n"
        f"소요:  {total_elapsed:.1f}초\n"
        f"로그:  {log_path}\n"
        f"요약:  {summary_path}\n"
        f"{border}\n"
    )
    print(final)

    if failed_step is not None:
        sys.exit(1)


if __name__ == '__main__':
    main()
