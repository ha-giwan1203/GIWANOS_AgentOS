import json, os, time, glob, subprocess, sys, pathlib

ROOT = r"C:\giwanos"
DISPATCH_DIR = os.path.join(ROOT, "data", "reports", "_dispatch")
PROCESSED_DIR = os.path.join(DISPATCH_DIR, "_processed")
FAILED_DIR = os.path.join(DISPATCH_DIR, "_failed")
os.makedirs(DISPATCH_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

# 선택적으로 존재할 수 있는 전송 스크립트 경로
SLACK_PY = os.path.join(ROOT, "scripts", "notify_slack.py")
NOTION_PY = os.path.join(ROOT, "tools", "notion_integration", "__init__.py")  # placeholder
PUSH_PY = os.path.join(ROOT, "scripts", "notify_push.py")  # (없으면 건너뜀)
EMAIL_PY = os.path.join(ROOT, "scripts", "notify_email.py")  # (없으면 건너뜀)

def try_send(cmd):
  try:
    print(f"[BRIDGE] run: {cmd}")
    # Windows: 파이썬 실행 우선순위 -> py -3 > python
    if cmd[0] == "PYTHON":
      exe = "py" if pathlib.Path(r"C:\Windows\py.exe").exists() else "python"
      cmd = [exe, "-3"] + cmd[1:]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(completed.stdout)
    if completed.returncode != 0:
      print(completed.stderr, file=sys.stderr)
      return False
    return True
  except Exception as e:
    print(f"[BRIDGE][ERR] {e}", file=sys.stderr)
    return False

def handle_ticket(ticket_path):
  with open(ticket_path, "r", encoding="utf-8") as f:
    t = json.load(f)

  ok_all = True
  send = t.get("send", {})
  arts = t.get("artifacts", [])

  # Slack
  if send.get("slack") and os.path.exists(SLACK_PY):
    for a in arts:
      if a.get("type") in ("markdown","pdf","txt","html"):
        ok = try_send(["PYTHON", SLACK_PY, "--title", a.get("title","artifact"), "--file", a["path"]])
        ok_all = ok_all and ok

  # Notion (여긴 적합한 통합 스크립트가 있으면 교체)
  if send.get("notion") and os.path.exists(NOTION_PY):
    # 예시: 별도 업로더가 있다면 여기서 호출
    pass

  # Push / Email - 스크립트 존재 시만 시도
  if send.get("push") and os.path.exists(PUSH_PY):
    for a in arts:
      try_send(["PYTHON", PUSH_PY, "--title", a.get("title","artifact"), "--file", a["path"]])

  if send.get("email") and os.path.exists(EMAIL_PY):
    for a in arts:
      try_send(["PYTHON", EMAIL_PY, "--title", a.get("title","artifact"), "--file", a["path"]])

  # 결과 정리
  target_dir = PROCESSED_DIR if ok_all else FAILED_DIR
  base = os.path.basename(ticket_path)
  os.replace(ticket_path, os.path.join(target_dir, base))
  print(f"[BRIDGE] {'OK' if ok_all else 'FAIL'} -> {base}")

def main(once=False):
  while True:
    tickets = sorted(glob.glob(os.path.join(DISPATCH_DIR, "dispatch_*.json")))
    if not tickets and once:
      print("[BRIDGE] no tickets. exit once-mode.")
      return
    for t in tickets:
      handle_ticket(t)
    if once:
      return
    time.sleep(5)

if __name__ == "__main__":
  once = "--once" in sys.argv
  main(once=once)
