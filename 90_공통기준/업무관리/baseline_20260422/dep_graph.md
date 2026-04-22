# Dependency Graph Matrix — 2026-04-22
# Plan glimmering-churning-reef 단계 0-A
# 활성 훅 37개 실측 + 쓰기/읽기/의존 관계

| Hook | Event(s) | Lines | Sources (bash deps) | Writes | Reads |
|------|----------|-------|---------------------|--------|-------|
| auto_compile.sh | PostToolUse(Write|Edit) | 42 | hook_common.sh | - | - |
| block_dangerous.sh | PreToolUse(Bash) | 88 | hook_common.sh | - | - |
| circuit_breaker_check.sh | SessionStart(*) | 49 | hook_common.sh | - | .claude/self/circuit_breaker.json, .claude/self/meta.json, .claude/self/meta_warn.log |
| commit_gate.sh | PreToolUse(Bash) | 182 | hook_common.sh | - | .claude/incident_ledger.jsonl |
| completion_gate.sh | Stop(*) | 170 | hook_common.sh | - | .claude/state/completion_gate_phase2b_last.txt |
| date_scope_guard.sh | PreToolUse(Bash) | 55 | hook_common.sh | - | - |
| debate_gate.sh | PreToolUse(mcp__Claude_in_Chrome__javascript_tool) | 70 | - | - | - |
| debate_independent_gate.sh | PreToolUse(mcp__Claude_in_Chrome__javascript_tool) | 49 | - | - | - |
| debate_send_gate_mark.sh | PostToolUse(mcp__Claude_in_Chrome__get_page_text) | 32 | - | - | - |
| debate_verify.sh | PreToolUse(Bash) | 195 | hook_common.sh | - | .claude/incident_ledger.jsonl |
| evidence_gate.sh | PreToolUse(Bash|Write|Edit|MultiEdit) | 208 | hook_common.sh | - | - |
| evidence_mark_read.sh | PostToolUse(Read|Grep|Glob|Bash|Write|Edit|MultiEdit) | 108 | hook_common.sh | - | .claude/state/active_domain.req, .claude/state/instruction_reads |
| evidence_stop_guard.sh | Stop(*) | 73 | hook_common.sh | - | - |
| gpt_followup_post.sh | PostToolUse(mcp__Claude_in_Chrome|Bash|Edit|Write) | 76 | hook_common.sh | - | - |
| gpt_followup_stop.sh | Stop(*) | 41 | hook_common.sh | - | - |
| handoff_archive.sh | PostToolUse(Write|Edit) | 111 | hook_common.sh | - | .claude/state/handoff_archive.lock |
| harness_gate.sh | PreToolUse(Bash) | 127 | - | - | - |
| health_check.sh | SessionStart(*) | 67 | hook_common.sh | - | .claude/self/HEALTH.md, .claude/self/diagnose.py, .claude/self/last_diagnosis.json, .claude/self/summary.txt |
| health_summary_gate.sh | UserPromptSubmit(*) | 65 | hook_common.sh | - | .claude/self/HEALTH.md, .claude/self/summary.txt, .claude/state/health_summary_first.ok |
| instruction_read_gate.sh | PreToolUse(Bash) | 84 | hook_common.sh | - | .claude/state/active_domain.req, .claude/state/instruction_reads |
| mcp_send_gate.sh | PreToolUse(mcp__Claude_in_Chrome__form_input) | 50 | - | - | .claude/state/instruction_reads |
| navigate_gate.sh | PreToolUse(mcp__Claude_in_Chrome__navigate) | 46 | - | - | - |
| notify_slack.sh | Notification(*) | 40 | hook_common.sh | - | - |
| permissions_sanity.sh | PreToolUse(Bash) | 103 | hook_common.sh | - | .claude/state/., .claude/state/permissions_sanity_last.txt |
| post_commit_notify.sh | PostToolUse(Bash) | 48 | hook_common.sh | - | - |
| precompact_save.sh | PreCompact(*) | 129 | hook_common.sh | - | - |
| protect_files.sh | PreToolUse(Write|Edit|MultiEdit) | 48 | hook_common.sh | - | - |
| quota_advisory.sh | PostToolUse(Bash) | 54 | hook_common.sh | - | .claude/self/quota_diagnose.py, 90_공통기준/protected_assets.yaml |
| risk_profile_prompt.sh | UserPromptSubmit(*) | 190 | hook_common.sh | - | .claude/state/active_domain.req |
| self_recovery_t1.sh | Stop(*) | 97 | hook_common.sh | - | .claude/self/auto_recovery.jsonl, .claude/self/circuit_breaker.json |
| session_start_restore.sh | SessionStart(*) | 207 | hook_common.sh | - | .claude/incident_ledger.jsonl, .claude/state/active_domain.req, .claude/state/instruction_reads, .claude/state/session_kernel.md, .claude/state/session_progress.json |
| skill_drift_check.sh | PreToolUse(Bash) | 86 | hook_common.sh | - | - |
| skill_instruction_gate.sh | PreToolUse(Bash) | 78 | hook_common.sh | - | - |
| state_rebind_check.sh | PreToolUse(Write|Edit|MultiEdit) | 62 | hook_common.sh | - | .claude/state/last_rebind_at, .claude/state/session_kernel.md |
| statusline.sh | statusLine | 35 | - | - | - |
| stop_guard.sh | Stop(*) | 85 | hook_common.sh | - | - |
| write_marker.sh | PostToolUse(Write|Edit) | 72 | hook_common.sh | - | - |

**총 활성 훅: 37**
**baseline 작성 시각: 2026-04-22T00:09:04.696180Z**