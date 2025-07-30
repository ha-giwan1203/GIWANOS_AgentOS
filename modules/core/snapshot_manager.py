
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('C:/giwanos/data/logs/snapshot_manager.log'),
        logging.StreamHandler()
    ],
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def create_incremental_snapshot():
    snapshot_dir = Path("C:/giwanos/data/snapshots/incremental_snapshot_" + datetime.now().strftime('%Y%m%d'))
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Incremental snapshot created at: {snapshot_dir}")

def create_full_snapshot():
    snapshot_dir = Path("C:/giwanos/data/snapshots/full_snapshot_" + datetime.now().strftime('%Y%m%d'))
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Full snapshot created at: {snapshot_dir}")
