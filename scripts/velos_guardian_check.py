import glob
import importlib
import json
import locale
import os
import sys
import time
from pathlib import Path

FAIL, WARN, PASS = "FAIL", "WARN", "PASS"
checks = []


def add(name, ok, msg_ok, msg_bad, level=None):
    level = level or (PASS if ok else FAIL)
    checks.append({"name": name, "status": level, "detail": msg_ok if ok else msg_bad})


def path(p):
    return str(Path(p).resolve())


# 1) 파이썬/venv 일치
venv_py = Path(r"C:\Users\User\venvs\velos\Scripts\python.exe")
add(
    "venv-exec",
    Path(sys.executable) == venv_py,
    f"exe={sys.executable}",
    f"exe={sys.executable} (!= {venv_py})",
)

# 2) 로케일/인코딩
enc = sys.stdout.encoding
pref = locale.getpreferredencoding(False)
lang = os.getenv("VELOS_LANG")
ok_loc = (enc or "").lower() == "utf-8" and (pref or "").lower().startswith("utf") and lang == "ko"
add(
    "locale-utf8",
    ok_loc,
    f"stdout={enc}, pref={pref}, VELOS_LANG={lang}",
    f"stdout={enc}, pref={pref}, VELOS_LANG={lang}",
)

# 3) MemoryAdapter 임포트
try:
    MA = importlib.import_module("modules.core.memory_adapter").MemoryAdapter
    add("memory-adapter", True, f"{MA}", "import failed")
except Exception as e:
    add("memory-adapter", False, "", f"{e}")

# 4) 보고서/디스패치 디렉터리 쓰기 가능
rep = Path(r"C:\giwanos\data\reports\auto")
rep.mkdir(parents=True, exist_ok=True)
disp = Path(r"C:\giwanos\data\reports\_dispatch")
disp.mkdir(parents=True, exist_ok=True)
try:
    tfile = rep / "guardian_touch.txt"
    tfile.write_text("ok", encoding="utf-8")
    add("reports-writable", True, path(tfile), "")
except Exception as e:
    add("reports-writable", False, "", f"{e}")

# 5) 최근 디스패치 파일 검증 + 전송 플래그 추정
dlist = sorted(glob.glob(r"C:\giwanos\data\reports\_dispatch\dispatch_*.json"))
if dlist:
    latest = Path(dlist[-1])
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
        flags = []
        for k in ("slack", "notion", "push", "email", "channel", "database"):
            if k in data:
                flags.append(f"{k}={data.get(k)}")
        add("dispatch-latest", True, f"{latest.name} | {'; '.join(flags) or 'no flags'}", "")
    except Exception as e:
        add("dispatch-latest", False, "", f"{latest.name}: {e}")
else:
    add("dispatch-latest", False, "", "no dispatch files")

# 6) system_health.json 로케일
sh = Path(r"C:\giwanos\data\logs\system_health.json")
if sh.exists():
    try:
        j = json.loads(sh.read_text(encoding="utf-8"))
        loc = j.get("locale")
        ok = loc in ("ko-KR", "ko_KR", "ko")
        add("ui-locale", ok, f"locale={loc}", f"locale={loc}")
    except Exception as e:
        add("ui-locale", False, "", f"{e}")
else:
    add("ui-locale", WARN, "missing", "system_health.json not found", level=WARN)

# 7) 폰트 TTF 유효성 (NanumGothic.ttf)
font = Path(r"C:\giwanos\fonts\NanumGothic.ttf")
if font.exists():
    try:
        from fontTools.ttLib import TTFont

        TTFont(str(font)).close()
        add("font-ttf", True, path(font), "")
    except Exception as e:
        add("font-ttf", False, "", f"{font.name}: {e}")
else:
    add("font-ttf", WARN, "NanumGothic.ttf not found", "missing", level=WARN)

# 8) Slack/Notion 토큰 존재 여부
sb = bool(os.getenv("SLACK_BOT_TOKEN"))
sc = bool(os.getenv("SLACK_CHANNEL") or os.getenv("SLACK_DEFAULT_CHANNEL"))
no = bool(os.getenv("NOTION_TOKEN"))
nd = bool(os.getenv("NOTION_DATABASE_ID"))
add("slack-env", sb and sc, f"SB={sb}, CH={sc}", f"SB={sb}, CH={sc}")
add("notion-env", no and nd, f"NT={no}, DB={nd}", f"NT={no}, DB={nd}")

# 9) JSON 직렬화 기본 정책
try:
    s = json.dumps({"msg": "한글 OK"}, ensure_ascii=False)
    ok = "한글" in s
    add("json-ensure-ascii", ok, s, s)
except Exception as e:
    add("json-ensure-ascii", False, "", f"{e}")

# 10) PYTHONPATH 점검
pp = os.getenv("PYTHONPATH", "")
ok_pp = ("C:\\giwanos" in pp) and ("modules" in pp)
add("pythonpath", ok_pp, pp, pp)

# 출력 요약
summary = {"PASS": 0, "WARN": 0, "FAIL": 0}
for c in checks:
    summary[c["status"]] = summary.get(c["status"], 0) + 1
print("=== VELOS Guardian Report ===")
for c in checks:
    tag = {"PASS": "✔", "WARN": "⚠", "FAIL": "✖"}[c["status"]]
    print(f"{tag} {c['name']}: {c['detail']}")
print(f"--- Totals: PASS={summary['PASS']} WARN={summary['WARN']} FAIL={summary['FAIL']}")
