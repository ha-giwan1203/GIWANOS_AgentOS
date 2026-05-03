---
name: token-threshold-warn
description: 저장소 문서 비대화 사전 감시 — TASKS/HANDOFF/MEMORY/incident 라인·바이트 측정 + 경고만 (차단 X)
grade: advisory
---

# Token Threshold Warn

> 임계치/구현/튜닝은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 트리거
- SessionStart hook 자동 (`session_start_restore.sh` 내부)
- 수동: `bash .claude/hooks/token_threshold_check.sh`

## 임계치 (3자 합의 고정)
| 대상 | 경고 | 강경고 |
|------|------|-------|
| TASKS.md | 400줄 | 800줄 |
| HANDOFF.md | 500줄 | 800줄 |
| MEMORY.md | 120줄 | 200줄 |
| 메모리 파일 수 | 60 | 100 |
| incident_ledger | 1MB | 3MB |

## verify
```bash
bash .claude/hooks/token_threshold_check.sh
# 경고 없으면 빈 출력 / 있으면 [WARN] 또는 [STRONG] 라인
```

## 정책 (요약)
- MUST: 경고만, 차단 도입 금지
- NEVER: 자동 아카이브 이동, 토큰 근사치 계산, hook 내부 승인 요청
- SHOULD: 강경고 3회 연속 → `hook_incident doc_drift` 자동 기록

## 실패 시
- advisory 등급, exit 0 강제 — 세션 계속
- 상세 → MANUAL.md "실패 대응" + "튜닝 가이드"
