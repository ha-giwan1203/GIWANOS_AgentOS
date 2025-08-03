import threading, time, shutil, pathlib, logging
def start_backup():
    def loop():
        while True:
            ts=time.strftime("%Y%m%d_%H%M"); dst=f"data/backups/memory_{ts}"
            shutil.make_archive(dst,"zip","data/memory")
            logging.getLogger("backup").info("백업완료 "+dst)
            time.sleep(3600)
    threading.Thread(target=loop,daemon=True).start()
