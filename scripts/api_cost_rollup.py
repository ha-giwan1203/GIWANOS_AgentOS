# =========================================================
# VELOS 운영 철학 선언문
# 1) 파일명 고정: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
# 2) 자가 검증 필수: 수정/배포 전 자동·수동 테스트를 통과해야 함
# 3) 실행 결과 직접 테스트: 코드 제공 시 실행 결과를 동봉/기록
# 4) 저장 경로 고정: ROOT=C:\giwanos 기준, 우회/추측 경로 금지
# 5) 실패 기록·회고: 실패 로그를 남기고 후속 커밋/문서에 반영
# 6) 기억 반영: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
# 7) 구조 기반 판단: 프로젝트 구조 기준으로만 판단 (추측 금지)
# 8) 중복/오류 제거: 불필요/중복 로직 제거, 단일 진실원칙 유지
# 9) 지능형 처리: 자동 복구·경고 등 방어적 설계 우선
# 10) 거짓 코드 절대 불가: 실행 불가·미검증·허위 출력 일체 금지
# =========================================================
from __future__ import annotations

import glob
import json

from modules.report_paths import ROOT

LOGS = ROOT / r"data\logs"
LOGS.mkdir(parents=True, exist_ok=True)


def main():
    # 규칙: data\logs\api_calls\*.jsonl 안의 각 줄에 {"cost": float}가 있다고 가정
    src_dir = LOGS / "api_calls"
    total = 0.0
    entries = 0
    if src_dir.exists():
        for fn in glob.glob(str(src_dir / "*.jsonl")):
            with open(fn, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        total += float(obj.get("cost", 0))
                        entries += 1
                    except Exception:
                        pass
    out = {"entries": entries, "total_cost": round(total, 6)}
    (LOGS / "api_cost_log.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] api_cost_log.json 갱신: entries={entries}, total={out['total_cost']}")


if __name__ == "__main__":
    main()
