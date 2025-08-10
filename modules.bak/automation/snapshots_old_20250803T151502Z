import os
from datetime import datetime

snapshot_dir = "C:/giwanos/data/snapshots"

def check_snapshots():
    if not os.path.exists(snapshot_dir):
        return "Snapshot directory does not exist."

    snapshots = os.listdir(snapshot_dir)
    if not snapshots:
        return "No snapshots found in the snapshot directory."

    latest_snapshot = max(snapshots, key=lambda f: os.path.getctime(os.path.join(snapshot_dir, f)))
    latest_snapshot_time = datetime.fromtimestamp(os.path.getctime(os.path.join(snapshot_dir, latest_snapshot)))

    return {
        "total_snapshots": len(snapshots),
        "latest_snapshot": latest_snapshot,
        "latest_snapshot_time": latest_snapshot_time.strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    result = check_snapshots()
    print(result)