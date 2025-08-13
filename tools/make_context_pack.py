import json, os, re
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
    out=[]
    for ln in lines:
        try:
            j = json.loads(ln.strip())
            txt = j.get("insight","")
            if any(k in txt for k in ["경로","VELOS_ROOT","하드코딩","규칙","목표","중요","주의"]):
                out.append(f"- {txt}")
        except Exception:
            pass
    return out[-50:]  # 너무 길면 자름

rules = ""
try:
    with open(RULES,"r",encoding="utf-8") as f:
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
with open(OUT,"w",encoding="utf-8") as f:
    f.write("\n\n".join(doc))
print(f"✅ CONTEXT_PACK 생성: {OUT}")
