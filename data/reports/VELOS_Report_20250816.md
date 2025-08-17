# VELOS Daily Report (20250816)

## Message Counters
- Last 5 minutes: **0**
- Last 60 minutes: **0**
- Last 24 hours: **0**

## Health Snapshot
```json
{
  "timestamp": 1755215423,
  "system_integrity": {
    "check_time": 1755215422,
    "file_issues": 0,
    "db_issues": 0,
    "process_issues": 1,
    "total_issues": 1,
    "integrity_ok": false,
    "details": {
      "file_issues": [],
      "db_issues": [],
      "process_issues": [
        "process_missing:autosave_runner"
      ]
    },
    "autosave_runner_count": 0,
    "autosave_runner_ok": false,
    "warnings": [
      "autosave_runner not running (required)"
    ]
  },
  "data_integrity": {
    "check_time": 1755215423,
    "memory_issues": 0,
    "db_issues": 0,
    "report_issues": 0,
    "total_issues": 0,
    "data_integrity_ok": true,
    "details": {
      "memory_issues": [],
      "db_issues": [],
      "report_issues": []
    }
  },
  "context_guard": {
    "flush_age_min": 9999,
    "context_age_min": 9999,
    "flush_ok": false,
    "context_ok": false,
    "checked_ts": 1755215423
  },
  "overall_status": "OK",
  "session_bootstrap_ts": 1755300106,
  "session_bootstrap_flush_moved": 0,
  "session_bootstrap_ok": true,
  "session_bootstrap_count": 16,
  "memory_tick_last_ts": 1755300423,
  "memory_tick_last_moved": 0,
  "memory_tick_last_ok": true,
  "memory_tick_stats": {
    "buffer_size": 0,
    "db_records": 8,
    "json_records": 53,
    "last_sync": 1755297147
  },
  "system_integrity_last_check": 1755302285,
  "system_integrity_ok": true,
  "system_integrity_issues": [],
  "data_integrity_last_check": 1755302285,
  "data_integrity_ok": true,
  "data_integrity_issues": [],
  "snapshot_last_sha256": "b593c33642e4ad7c22278764d002f8281996d76ca4e5e44c147b96ceca5dbda9",
  "snapshot_last_file": "snapshot_20250815_0905.zip",
  "snapshot_last_ts": 1755216333,
  "snapshot_last_size": 148811,
  "snapshot_integrity_ok": true,
  "snapshot_integrity_last_check": 1755216333,
  "snapshot_catalog_last_update": 1755280982,
  "snapshot_catalog_entries": 15,
  "snapshot_catalog_total_files": 15,
  "snapshot_catalog_updated_count": 0,
  "snapshot_verify_last_ts": 1755301319,
  "snapshot_verify_checked": 15,
  "snapshot_verify_mismatches": [],
  "snapshot_verify_missing": [],
  "snapshot_verify_ok": true,
  "snapshot_verify_total_files": 15,
  "snapshot_verify_verified_files": 15,
  "hotbuf_last_build_ts": 1755296347,
  "hotbuf_ttl_sec": 7200,
  "hotbuf_ok": true,
  "hotbuf_rebuild_count": 2,
  "context_build_last_ts": 1755302018,
  "context_build_last_count": 4,
  "context_build_last_ok": true,
  "last_append_ok": true,
  "last_append_ts": 1755297146,
  "last_flush_count": 2,
  "last_flush_ok": true,
  "last_flush_ts": 1755297147,
  "memory_pipeline_last_test_ts": 1755257296,
  "memory_pipeline_last_test_ok": true,
  "cursor_state_reconciled": true,
  "cursor_state": {
    "file_flag": false,
    "env_flag": false,
    "expired": false,
    "final": false
  },
  "runtime_state": {
    "cursor": {
      "schema_version": 1,
      "cursor_in_use": false,
      "env_cursor_in_use": false,
      "source": "test_thread_done",
      "last_update_utc": "2025-08-15T22:37:13Z",
      "expired": false,
      "ttl_minutes": 30,
      "state_path": "C:\\giwanos\\data\\memory\\runtime_state.json",
      "reconciled": {
        "file_flag": false,
        "env_flag": false,
        "expired": false,
        "final": false
      }
    },
    "environment": {
      "CURSOR_IN_USE": "0",
      "VELOS_SESSION_SOURCE": null,
      "VELOS_RUNTIME_STATE_PATH": null
    },
    "reconciled": {
      "file_flag": false,
      "env_flag": false,
      "expired": false,
      "final": false
    }
  },
  "last_runtime_check": 1755297561,
  "cursor_in_use": false,
  "session_source": "unknown"
}
```
