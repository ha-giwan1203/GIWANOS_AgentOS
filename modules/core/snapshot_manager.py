
import logging
import sys
from datetime import datetime

logger = logging.getLogger("snapshot_manager")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(logging.FileHandler('C:/giwanos/data/logs/snapshot_manager.log'))
    logger.addHandler(logging.StreamHandler(sys.stdout))

def create_incremental_snapshot():
    timestamp = datetime.now().strftime('%Y%m%d')
    snapshot_path = f'C:/giwanos/data/snapshots/incremental_snapshot_{timestamp}'
    logger.info(f"Incremental snapshot created at: {snapshot_path}")

def create_full_snapshot():
    timestamp = datetime.now().strftime('%Y%m%d')
    snapshot_path = f'C:/giwanos/data/snapshots/full_snapshot_{timestamp}'
    logger.info(f"Full snapshot created at: {snapshot_path}")

if __name__ == '__main__':
    create_incremental_snapshot()
