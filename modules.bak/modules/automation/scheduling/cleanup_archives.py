"""Cleanup & Archive – reports/logs 정리."""
import pathlib, shutil, datetime, zipfile, logging

BASE   = pathlib.Path(__file__).resolve().parents[3]       # giwanos
REPORT = BASE / "data/reports"
LOGDIR = BASE / "data/logs"
ARCH   = BASE / "data/archive"; ARCH.mkdir(exist_ok=True)

KEEP_DAYS = 30      # 30일 초과 → ZIP
DELETE_MONTH = 6    # ZIP 6개월 초과 → 삭제

log = logging.getLogger("cleanup_archives")

def zip_old(folder: pathlib.Path):
    today = datetime.datetime.utcnow().date()
    for fp in folder.glob("*.*"):
        if not fp.is_file(): continue
        age = (today - datetime.date.fromtimestamp(fp.stat().st_mtime)).days
        if age > KEEP_DAYS:
            zip_name = ARCH / f"{fp.stem}.zip"
            with zipfile.ZipFile(zip_name, "a", zipfile.ZIP_DEFLATED) as z:
                z.write(fp, arcname=fp.name)
            fp.unlink()
            log.info("Archived %s → %s", fp.name, zip_name.name)

def delete_old_zips():
    today = datetime.datetime.utcnow().date()
    for zp in ARCH.glob("*.zip"):
        age_month = (today.year - zp.stat().st_mtime // (60*60*24*30)) * 12 + \
                    (today.month - datetime.datetime.utcfromtimestamp(zp.stat().st_mtime).month)
        if age_month > DELETE_MONTH:
            zp.unlink(); log.info("Deleted old archive %s", zp.name)

if __name__ == "__main__":
    zip_old(REPORT); zip_old(LOGDIR); delete_old_zips()
    print("✅ Cleanup & archive finished.")


