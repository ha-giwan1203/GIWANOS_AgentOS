# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=/home/user/webapp 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

from modules.report_paths import ROOT

REPORTS = ROOT / r"data\reports"
ENV = ROOT / r"configs\.env"


def load_env():
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def latest_pdf():
    files = list(REPORTS.glob("velos_report_*.pdf"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def main():
    load_env()
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        print("[SKIP] SLACK_WEBHOOK_URL 미설정")
        return 0
    p = latest_pdf()
    if not p:
        print("[SKIP] 최신 PDF 없음")
        return 0
    text = f"VELOS 보고서 생성: {p.name}\\n경로: {p}"
    body = json.dumps({"text": text}).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urlopen(req).read()
        print("[OK] Slack 알림 전송")
    except Exception as e:
        print("[WARN] Slack 전송 실패:", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
