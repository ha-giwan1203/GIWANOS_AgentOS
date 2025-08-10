"""VELOS system_health.json 마이그레이션 스크립트
   - *_usage_percent → *_percent 로 키명 통일
   - 실행 전: data/logs/system_health.json 백업 권장
"""
import json, pathlib, shutil, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]          # C:\giwanos
LOG  = ROOT / "data" / "logs" / "system_health.json"
BACK = LOG.with_suffix(".bak")

ALIAS = {
    "cpu_usage_percent":    "cpu_percent",
    "memory_usage_percent": "memory_percent",
    "disk_usage_percent":   "disk_percent",
}

def migrate():
    if not LOG.exists():
        print("❌ Log file not found:", LOG); return
    # 1) 백업
    if not BACK.exists():
        shutil.copy(LOG, BACK)
        print("🗄️  Backup created →", BACK.name)
    # 2) 변환
    data = json.loads(LOG.read_text(encoding="utf-8"))
    if isinstance(data, dict):      # 단일 객체일 경우 리스트로
        data = [data]
    changed = False
    for row in data:
        for old, new in ALIAS.items():
            if old in row and new not in row:
                row[new] = row.pop(old)
                changed = True
    # 3) 저장
    if changed:
        LOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("✅ Migration complete — keys unified.")
    else:
        print("ℹ️  No outdated keys found. Nothing to change.")

if __name__ == "__main__":
    migrate()


