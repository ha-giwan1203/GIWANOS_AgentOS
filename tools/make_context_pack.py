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
import json
import os
import re
from datetime import datetime

BASE = r"C:\giwanos"
MEM = os.path.join(BASE, "data", "memory", "learning_memory.json")
RULES = os.path.join(BASE, "docs", "RULES.md")
OUT = os.path.join(BASE, "docs", "CONTEXT_PACK.md")


def tail(path, n=200):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-n:]
    except FileNotFoundError:
        return []


def extract_highlights(lines):
    out = []
    for ln in lines:
        try:
            j = json.loads(ln.strip())
            txt = j.get("insight", "")
            if any(
                k in txt for k in ["경로", "VELOS_ROOT", "하드코딩", "규칙", "목표", "중요", "주의"]
            ):
                out.append(f"- {txt}")
        except Exception:
            pass
    return out[-50:]  # 너무 길면 자름


rules = ""
try:
    with open(RULES, "r", encoding="utf-8") as f:
        rules = f.read()
except FileNotFoundError:
    rules = "# RULES\n(규칙 파일 없음)"

mem_tail = tail(MEM, n=500)
hi = extract_highlights(mem_tail)

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
doc = []
doc.append(f"# CONTEXT PACK  ({now})")
doc.append("## 핵심 규칙 요약")
doc.append(rules.strip())
doc.append("## 최근 메모리 하이라이트(최대 50)")
doc.extend(hi if hi else ["- 최근 하이라이트 없음"])
doc.append("## 작업 상태 체크리스트")
doc.append("- 경로: VELOS_ROOT 만 사용, 절대경로 금지")
doc.append("- 테스트 실패시: 최소 수정 원칙")
doc.append("- 변경은 PR 브랜치에서만, main은 보호")
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n\n".join(doc))
print(f"✅ CONTEXT_PACK 생성: {OUT}")
