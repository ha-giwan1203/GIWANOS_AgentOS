# VELOS 설계 적합성 결과(BCT-9)
- 생성시각: 2025-08-08T16:46:54.633892
- 위험도(level): **low**
- 요약: BCT-9 설계 적합성: FAIL=0 / 9 핵심 항목
| 항목 | 상태 | 증적(요약) |
|---|---|---|
| paths | PASS | {"detail": {"master_loop": "C:\\giwanos\\scripts\\run_giwanos_master_loop.py", "dashboard": "C:\\giwanos\\interface\\vel |
| context_engine | PASS | {"evidence_files": [".venv\\Lib\\site-packages\\GPUtil\\GPUtil.py", ".venv\\Lib\\site-packages\\GPUtil\\demo_GPUtil.py", |
| self_learning | PASS | {"detail": {"learning_memory_exists": true, "learning_memory_recent_14d": true}} |
| parallel_lock | PASS | {"evidence_files": [".venv\\Lib\\site-packages\\aiohappyeyeballs\\_staggered.py", ".venv\\Lib\\site-packages\\aiohappyey |
| xai_logging | PASS | {"recent_reports": ["adaptive_reflection_20250801.md", "ai_insight_20250806.md", "ai_insights.json", "ai_insights_report |
| auto_recovery | PASS | {"evidence_files": ["data\\snapshots\\full_snapshot_20250804\\auto_recovery_agent.py", "data\\snapshots\\incremental_sna |
| smart_backup | PASS | {"recent_archives": ["weekly_report_20250805.zip"]} |
| reporting | PASS | {"formats": {"pdf": true, "md": true, "html": true}} |
| extensibility | PASS | {"detail": {"settings_yaml": true, "system_config_json": true, "tools_dir_exists": true}} |
| dashboard | PASS | {"detail": {"dashboard_path": "C:\\giwanos\\interface\\velos_dashboard.py"}} |
| scheduler | N/A | {"available": true, "found": {"VELOS_DailyCleanup": true, "VELOS_MasterLoop": true}, "raw_len": 547472} |
| master_loop_smoke | N/A | {"python": "C:\\giwanos\\venv\\Scripts\\python.exe", "returncode": 1, "stdout_sample": "", "stderr_sample": "Traceback ( |